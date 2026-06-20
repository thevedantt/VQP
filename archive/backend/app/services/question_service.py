"""Loads and serves the curated PYQ question bank (labeled_questions.json).

This is the canonical source of previous-year-question (PYQ) data: each
entry has been AI-labeled with chapter, concept, difficulty and diagram
metadata, which makes it directly usable for chapter/type/marks based
selection without any further enrichment.
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path

from app.core.exceptions import DataLoadError
from app.models.enums import QuestionType

logger = logging.getLogger(__name__)

# Maps the long-form question type strings used in the dataset to the
# short, canonical codes used throughout the API.
TYPE_CODE_MAP: dict[str, QuestionType] = {
    "MCQ": "MCQ",
    "Very Short Answer (VSA)": "VSA",
    "Short Answer (SA)": "SA",
    "Long Answer (LA)": "LA",
    "Case Study": "Case Study",
    "Assertion Reason": "Assertion Reason",
}

# Canonical marks associated with each question type, derived from the
# dataset's marks distribution. Used as a fallback when generating new
# (AI) questions of a given type.
TYPE_MARKS_MAP: dict[QuestionType, int] = {
    "MCQ": 1,
    "Assertion Reason": 1,
    "VSA": 2,
    "SA": 3,
    "Case Study": 4,
    "LA": 5,
}


@dataclass(frozen=True)
class PYQQuestion:
    """A single previous-year question, normalized for API consumption."""

    question_id: str
    source_file: str
    section: str
    type: QuestionType
    marks: int
    chapter: str
    concept: str | None
    difficulty: str
    question: str
    options: dict[str, str] = field(default_factory=dict)
    requires_diagram: bool = False
    diagram_type: str = "none"


class QuestionService:
    """In-memory access layer over the labeled PYQ question bank."""

    def __init__(self, labeled_questions_path: Path) -> None:
        self._path = labeled_questions_path
        self._questions: list[PYQQuestion] = self._load(labeled_questions_path)
        self._by_id: dict[str, PYQQuestion] = {q.question_id: q for q in self._questions}
        logger.info("QuestionService loaded %d PYQ questions from %s", len(self._questions), labeled_questions_path)

    @staticmethod
    def _load(path: Path) -> list[PYQQuestion]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise DataLoadError(f"Question bank file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise DataLoadError(f"Question bank file is not valid JSON: {path}") from exc

        questions: list[PYQQuestion] = []
        for entry in raw:
            chapter = entry.get("chapter")
            if not chapter:
                # Entries without a confirmed chapter cannot be placed into a
                # chapter-weighted paper, so they are excluded from the pool.
                continue

            raw_type = entry.get("type", "")
            question_type = TYPE_CODE_MAP.get(raw_type, raw_type)

            questions.append(
                PYQQuestion(
                    question_id=entry["question_id"],
                    source_file=entry.get("source_file", ""),
                    section=entry.get("section", ""),
                    type=question_type,  # type: ignore[arg-type]
                    marks=entry.get("marks", TYPE_MARKS_MAP.get(question_type, 1)),  # type: ignore[arg-type]
                    chapter=chapter,
                    concept=entry.get("concept"),
                    difficulty=entry.get("difficulty", "medium"),
                    question=entry.get("question", ""),
                    options=entry.get("options") or {},
                    requires_diagram=entry.get("requires_diagram", False),
                    diagram_type=entry.get("diagram_type", "none"),
                )
            )
        return questions

    def get_all(self) -> list[PYQQuestion]:
        """Return every loaded PYQ question."""

        return list(self._questions)

    def get_by_id(self, question_id: str) -> PYQQuestion | None:
        """Look up a single question by its dataset ID."""

        return self._by_id.get(question_id)

    def get_chapters(self) -> list[str]:
        """Return the sorted list of distinct chapters present in the question bank."""

        return sorted({q.chapter for q in self._questions})

    def filter(
        self,
        chapters: list[str] | None = None,
        question_type: QuestionType | None = None,
        marks: int | None = None,
        difficulty: str | None = None,
        requires_diagram: bool | None = None,
    ) -> list[PYQQuestion]:
        """Return questions matching all of the provided (optional) criteria."""

        chapter_set = set(chapters) if chapters else None
        result = []
        for q in self._questions:
            if chapter_set is not None and q.chapter not in chapter_set:
                continue
            if question_type is not None and q.type != question_type:
                continue
            if marks is not None and q.marks != marks:
                continue
            if difficulty is not None and q.difficulty != difficulty:
                continue
            if requires_diagram is not None and q.requires_diagram != requires_diagram:
                continue
            result.append(q)
        return result

    def get_type_distribution(self, chapters: list[str] | None = None) -> dict[str, int]:
        """Return question counts per question type, optionally scoped to a set of chapters."""

        chapter_set = set(chapters) if chapters else None
        counts: dict[str, int] = {}
        for q in self._questions:
            if chapter_set is not None and q.chapter not in chapter_set:
                continue
            counts[q.type] = counts.get(q.type, 0) + 1
        return counts

    def sample(
        self,
        chapter: str,
        question_type: QuestionType,
        marks: int | None = None,
        exclude_ids: set[str] | None = None,
        requires_diagram: bool | None = None,
        rng: random.Random | None = None,
    ) -> PYQQuestion | None:
        """Pick a random question for the given chapter/type, relaxing constraints if needed.

        Falls back progressively: (chapter, type, marks) -> (chapter, type) ->
        (chapter, any type) -> None if the chapter has no questions at all.

        When ``requires_diagram`` is True, the constraint is never relaxed -
        callers should fall back to AI generation instead if no diagram-bearing
        PYQ candidate exists for the chapter.
        """

        rng = rng or random
        exclude_ids = exclude_ids or set()

        if requires_diagram:
            candidates = [
                q
                for q in self.filter(chapters=[chapter], question_type=question_type, marks=marks, requires_diagram=True)
                if q.question_id not in exclude_ids
            ]
            if not candidates:
                candidates = [
                    q
                    for q in self.filter(chapters=[chapter], question_type=question_type, requires_diagram=True)
                    if q.question_id not in exclude_ids
                ]
            if not candidates:
                candidates = [
                    q
                    for q in self.filter(chapters=[chapter], requires_diagram=True)
                    if q.question_id not in exclude_ids
                ]
            if not candidates:
                return None
            return rng.choice(candidates)

        candidates = [
            q
            for q in self.filter(chapters=[chapter], question_type=question_type, marks=marks)
            if q.question_id not in exclude_ids
        ]
        if not candidates:
            candidates = [
                q
                for q in self.filter(chapters=[chapter], question_type=question_type)
                if q.question_id not in exclude_ids
            ]
        if not candidates:
            candidates = [q for q in self.filter(chapters=[chapter]) if q.question_id not in exclude_ids]
        if not candidates:
            return None

        return rng.choice(candidates)
