"""Balanced Paper Service.

Given a chapter weightage (percentages) and a generation request, this
service decides exactly which (chapter, question type, marks) "slots" make
up the paper, then fills each slot either from the PYQ question bank or via
the Gemini question generator according to ``pyq_percentage`` /
``ai_percentage``.

It also runs the **Diagram Coverage Engine**: a target number of slots are
flagged with a ``diagram_hint`` (one of the five priority diagram types) so
that approximately ``diagram_percentage`` of the paper ends up requiring a
diagram, sourced from either diagram-labeled PYQs or diagram-aware AI
generation.

Final diagram specification/SVG generation and response assembly are handled
by the orchestrator - this service only produces a balanced set of
diagram-annotated question drafts.
"""

from __future__ import annotations

import itertools
import logging
import random
import re
from dataclasses import dataclass, field, replace

from app.core.exceptions import GeminiServiceError, OpenRouterServiceError
from app.models.enums import DifficultyLevel, DiagramType, QuestionSource, QuestionType
from app.models.requests import GeneratePaperRequest
from app.services import local_question_generator
from app.services.allocation import allocate_largest_remainder
from app.services.book_service import BookService
from app.services.diagram_service import DiagramService
from app.services.gemini_service import GeminiService
from app.services.openrouter_service import OpenRouterService
from app.services.question_service import TYPE_MARKS_MAP, QuestionService

logger = logging.getLogger(__name__)

# Diagram types considered for the coverage engine, in priority order.
_PRIORITY_DIAGRAM_TYPES: list[DiagramType] = ["free_body", "circuit", "ray_diagram", "graph", "magnetic_field"]

# Question types for which "Draw/Sketch/Plot ..." instructions read naturally.
_DIAGRAM_FRIENDLY_TYPES: set[QuestionType] = {"SA", "LA", "VSA", "Case Study"}

# Per-chapter affinity: which diagram types are topically plausible for a
# question drawn from that chapter. Used to prefer sensible (chapter, diagram
# type) pairings when assigning diagram hints; falls back to ["graph"] for
# chapters not listed here.
_CHAPTER_DIAGRAM_AFFINITY: dict[str, list[DiagramType]] = {
    "Electric Charges and Fields": ["free_body", "graph"],
    "Electrostatic Potential and Capacitance": ["circuit", "graph"],
    "Current Electricity": ["circuit", "graph"],
    "Moving Charges and Magnetism": ["magnetic_field", "free_body", "graph"],
    "Magnetism and Matter": ["magnetic_field", "graph"],
    "Electromagnetic Induction": ["circuit", "magnetic_field", "graph"],
    "Alternating Current": ["circuit", "graph"],
    "Electromagnetic Waves": ["graph"],
    "Ray Optics": ["ray_diagram", "graph"],
    "Wave Optics": ["ray_diagram", "graph"],
    "Dual Nature of Radiation and Matter": ["graph"],
    "Atoms": ["ray_diagram", "graph"],
    "Nuclei": ["graph"],
    "Semiconductor Electronics": ["circuit", "graph"],
    "Electron Microscopy and X-ray Diffraction": ["ray_diagram", "graph"],
}
_DEFAULT_DIAGRAM_AFFINITY: list[DiagramType] = ["graph"]


@dataclass(frozen=True)
class QuestionDraft:
    """A question selected/generated for inclusion in a paper, diagram-annotated."""

    question_id: str
    source: QuestionSource
    type: QuestionType
    marks: int
    chapter: str
    difficulty: DifficultyLevel
    question: str
    options: dict[str, str] = field(default_factory=dict)
    concept: str | None = None
    requires_diagram: bool = False
    diagram_type: DiagramType = "none"
    diagram_entities: list[str] = field(default_factory=list)
    diagram_scenario: str | None = None


@dataclass(frozen=True)
class PaperPlan:
    """The result of allocating and filling all question slots for a paper."""

    pyq_questions: list[QuestionDraft]
    ai_questions: list[QuestionDraft]
    chapter_distribution: dict[str, int]
    type_distribution: dict[str, int]


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


@dataclass(frozen=True)
class _Slot:
    chapter: str
    question_type: QuestionType
    marks: int
    source: QuestionSource
    diagram_hint: DiagramType | None = None


def _normalize_diagram(requires_diagram: bool, diagram_type: DiagramType) -> tuple[bool, DiagramType]:
    """``diagram_type == "none"`` can never be rendered, so it always implies ``requires_diagram = False``."""

    if diagram_type == "none":
        return False, "none"
    return requires_diagram, diagram_type


def _affinity_for(chapter: str) -> list[DiagramType]:
    return _CHAPTER_DIAGRAM_AFFINITY.get(chapter, _DEFAULT_DIAGRAM_AFFINITY)


def _pick_slot_for_diagram(slots: list[_Slot], order: list[int], assigned: set[int], diagram_type: DiagramType) -> int | None:
    """Pick the best-fit unassigned slot for ``diagram_type``.

    Preference order: (diagram-friendly type AND chapter affinity match) ->
    (diagram-friendly type) -> (chapter affinity match) -> (any slot).
    """

    for idx in order:
        if idx not in assigned and slots[idx].question_type in _DIAGRAM_FRIENDLY_TYPES and diagram_type in _affinity_for(slots[idx].chapter):
            return idx
    for idx in order:
        if idx not in assigned and slots[idx].question_type in _DIAGRAM_FRIENDLY_TYPES:
            return idx
    for idx in order:
        if idx not in assigned and diagram_type in _affinity_for(slots[idx].chapter):
            return idx
    for idx in order:
        if idx not in assigned:
            return idx
    return None


def _assign_diagram_hints(slots: list[_Slot], diagram_target: int, rng: random.Random) -> list[_Slot]:
    """Flag ``diagram_target`` slots with a priority diagram type hint."""

    if diagram_target <= 0 or not slots:
        return slots

    diagram_target = min(diagram_target, len(slots))
    order = list(range(len(slots)))
    rng.shuffle(order)

    hints: dict[int, DiagramType] = {}
    assigned: set[int] = set()
    type_cycle = itertools.cycle(_PRIORITY_DIAGRAM_TYPES)

    for _ in range(diagram_target):
        diagram_type = next(type_cycle)
        chosen = _pick_slot_for_diagram(slots, order, assigned, diagram_type)
        if chosen is None:
            break
        hints[chosen] = diagram_type
        assigned.add(chosen)

    return [replace(slot, diagram_hint=hints.get(i)) for i, slot in enumerate(slots)]


class PaperService:
    """Allocates question slots across chapters/types and fills them PYQ vs AI."""

    def __init__(
        self,
        question_service: QuestionService,
        book_service: BookService,
        gemini_service: GeminiService,
        openrouter_service: OpenRouterService,
        diagram_service: DiagramService,
    ) -> None:
        self._question_service = question_service
        self._book_service = book_service
        self._gemini_service = gemini_service
        self._openrouter_service = openrouter_service
        self._diagram_service = diagram_service

    def generate(
        self,
        request: GeneratePaperRequest,
        chapter_weightage: dict[str, int],
        rng: random.Random | None = None,
    ) -> PaperPlan:
        """Build a balanced paper plan from a chapter weightage and request settings."""

        rng = rng or random
        scope = list(chapter_weightage.keys())

        chapter_counts = allocate_largest_remainder(chapter_weightage, request.total_questions)
        slots = self._build_slots(scope, chapter_counts)

        source_counts = allocate_largest_remainder(
            {"pyq": request.pyq_percentage, "ai": request.ai_percentage}, len(slots)
        )
        slots = self._assign_sources(slots, source_counts, rng)

        diagram_target = 0
        if request.include_diagrams and slots:
            diagram_target = round(len(slots) * request.diagram_percentage / 100)
        slots = _assign_diagram_hints(slots, diagram_target, rng)

        pyq_questions: list[QuestionDraft] = []
        ai_questions: list[QuestionDraft] = []
        used_pyq_ids: set[str] = set()
        ai_counter = 0

        for slot in slots:
            if slot.source == "pyq":
                draft = self._fill_pyq_slot(slot, used_pyq_ids, request.include_diagrams, rng)
                if draft is not None:
                    pyq_questions.append(draft)
                    used_pyq_ids.add(draft.question_id)
                    continue
                # No PYQ available for this slot (or none satisfying the
                # diagram requirement) - fall back to AI generation instead.
                logger.info(
                    "No PYQ available for chapter='%s' type=%s diagram_hint=%s; generating with AI instead.",
                    slot.chapter, slot.question_type, slot.diagram_hint,
                )

            ai_counter += 1
            ai_questions.append(self._fill_ai_slot(slot, request.difficulty, ai_counter, request.include_diagrams))

        chapter_distribution = self._count_by(pyq_questions + ai_questions, key=lambda d: d.chapter)
        type_distribution = self._count_by(pyq_questions + ai_questions, key=lambda d: d.type)

        return PaperPlan(
            pyq_questions=pyq_questions,
            ai_questions=ai_questions,
            chapter_distribution=chapter_distribution,
            type_distribution=type_distribution,
        )

    def _build_slots(self, scope: list[str], chapter_counts: dict[str, int]) -> list[_Slot]:
        slots: list[_Slot] = []
        for chapter in scope:
            count = chapter_counts.get(chapter, 0)
            if count <= 0:
                continue

            type_weights = self._question_service.get_type_distribution(chapters=[chapter])
            type_counts = allocate_largest_remainder(type_weights, count)

            for question_type, type_count in type_counts.items():
                for _ in range(type_count):
                    slots.append(
                        _Slot(
                            chapter=chapter,
                            question_type=question_type,  # type: ignore[arg-type]
                            marks=TYPE_MARKS_MAP.get(question_type, 1),  # type: ignore[arg-type]
                            source="pyq",
                        )
                    )
        return slots

    @staticmethod
    def _assign_sources(slots: list[_Slot], source_counts: dict[str, int], rng: random.Random) -> list[_Slot]:
        shuffled = list(slots)
        rng.shuffle(shuffled)

        num_pyq = source_counts.get("pyq", 0)
        result: list[_Slot] = []
        for i, slot in enumerate(shuffled):
            source: QuestionSource = "pyq" if i < num_pyq else "ai"
            result.append(_Slot(chapter=slot.chapter, question_type=slot.question_type, marks=slot.marks, source=source))
        return result

    def _fill_pyq_slot(self, slot: _Slot, used_ids: set[str], include_diagrams: bool, rng: random.Random) -> QuestionDraft | None:
        if slot.diagram_hint is not None:
            question = self._question_service.sample(
                chapter=slot.chapter,
                question_type=slot.question_type,
                marks=slot.marks,
                exclude_ids=used_ids,
                requires_diagram=True,
                rng=rng,
            )
            if question is None:
                # No diagram-bearing PYQ available for this slot - let the
                # caller fall back to diagram-aware AI generation.
                return None
            requires_diagram = True
            diagram_type: DiagramType = question.diagram_type  # type: ignore[assignment]
            if diagram_type == "none":
                # labeled_questions.json only distinguishes "circuit" vs
                # "none" - cross-check against the richer diagram_dataset.json
                # (via detect()) for the actual diagram type, falling back to
                # the slot's hint (always one of the five priority types).
                detection = self._diagram_service.detect(question.question, question_id=question.question_id)
                diagram_type = detection.diagram_type if detection.diagram_type != "none" else slot.diagram_hint
        else:
            question = self._question_service.sample(
                chapter=slot.chapter,
                question_type=slot.question_type,
                marks=slot.marks,
                exclude_ids=used_ids,
                rng=rng,
            )
            if question is None:
                return None

            if include_diagrams:
                detection = self._diagram_service.detect(question.question, question_id=question.question_id)
                requires_diagram, diagram_type = _normalize_diagram(detection.requires_diagram, detection.diagram_type)
            else:
                requires_diagram, diagram_type = False, "none"

        return QuestionDraft(
            question_id=question.question_id,
            source="pyq",
            type=question.type,
            marks=question.marks,
            chapter=question.chapter,
            difficulty=question.difficulty,  # type: ignore[arg-type]
            question=question.question,
            options=question.options,
            concept=question.concept,
            requires_diagram=requires_diagram,
            diagram_type=diagram_type,
        )

    def _fill_ai_slot(self, slot: _Slot, difficulty: DifficultyLevel, sequence: int, include_diagrams: bool) -> QuestionDraft:
        excerpt = self._book_service.get_excerpt(slot.chapter, max_chars=2500)

        require_diagram = include_diagrams and slot.diagram_hint is not None
        diagram_type_hint = slot.diagram_hint if require_diagram else None

        try:
            generated = self._openrouter_service.generate_question(
                chapter=slot.chapter,
                difficulty=difficulty,
                marks=slot.marks,
                question_type=slot.question_type,
                context=excerpt,
                require_diagram=require_diagram,
                diagram_type_hint=diagram_type_hint,
            )
        except OpenRouterServiceError as exc:
            logger.warning(
                "OpenRouter generation failed for chapter='%s' type=%s; falling back to Gemini. %s",
                slot.chapter, slot.question_type, exc.message,
            )
            try:
                generated = self._gemini_service.generate_question(
                    chapter=slot.chapter,
                    difficulty=difficulty,
                    marks=slot.marks,
                    question_type=slot.question_type,
                    context=excerpt,
                    require_diagram=require_diagram,
                    diagram_type_hint=diagram_type_hint,
                )
            except GeminiServiceError as exc2:
                logger.warning(
                    "Gemini generation failed for chapter='%s' type=%s; using local generator. %s",
                    slot.chapter, slot.question_type, exc2.message,
                )
                generated = local_question_generator.generate(
                    chapter=slot.chapter,
                    difficulty=difficulty,
                    marks=slot.marks,
                    question_type=slot.question_type,
                    context=excerpt,
                    require_diagram=require_diagram,
                    diagram_type_hint=diagram_type_hint,
                )

        if include_diagrams:
            detection = self._diagram_service.detect(generated["question"])
            requires_diagram, diagram_type = _normalize_diagram(detection.requires_diagram, detection.diagram_type)
        else:
            requires_diagram, diagram_type = False, "none"

        question_id = f"AI_{_slugify(slot.chapter)}_{sequence:03d}"
        return QuestionDraft(
            question_id=question_id,
            source="ai",
            type=generated["type"],
            marks=generated["marks"],
            chapter=generated["chapter"],
            difficulty=generated["difficulty"],
            question=generated["question"],
            options=generated.get("options", {}),
            concept=generated.get("concept"),
            requires_diagram=requires_diagram,
            diagram_type=diagram_type,
            diagram_entities=generated.get("diagram_entities", []) if requires_diagram else [],
            diagram_scenario=generated.get("diagram_scenario") if requires_diagram else None,
        )

    @staticmethod
    def _count_by(drafts: list[QuestionDraft], key) -> dict[str, int]:
        counts: dict[str, int] = {}
        for draft in drafts:
            k = key(draft)
            counts[k] = counts.get(k, 0) + 1
        return counts
