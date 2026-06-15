"""Paper Generation Orchestrator - the brain of VisualQ Pilot.

Coordinates the full generation pipeline:

    Weightage Engine -> PYQ Selector / NCERT Retrieval / Gemini Generator
    -> Diagram Coverage Engine -> Diagram Spec + SVG Generation
    -> Paper Assembly -> Final Paper
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.models.requests import GeneratePaperRequest
from app.models.responses import DiagramCoverage, DiagramSpec, GeneratedPaperResponse, PaperSection, QuestionItem
from app.services.diagram_service import DiagramService
from app.services.diagram_svg import render_svg
from app.services.diagram_template_service import DiagramTemplateService
from app.services.paper_evaluator import PaperEvaluator
from app.services.paper_service import PaperService, QuestionDraft
from app.services.physics_understanding_service import PhysicsUnderstandingService
from app.services.schema_population_service import SchemaPopulationService
from app.services.weightage_service import WeightageService

logger = logging.getLogger(__name__)

# Diagram types tracked individually in the DiagramCoverage analytics.
_TRACKED_DIAGRAM_TYPES = ("free_body", "circuit", "ray_diagram", "graph", "magnetic_field")

# Difficulty progression order used to sort questions within a section.
_DIFFICULTY_ORDER: dict[str, int] = {"easy": 0, "medium": 1, "hard": 2}

# CBSE-style section definitions, in paper order. Each section groups the
# question types that share its marks-per-question value.
_SECTION_DEFS: list[dict] = [
    {
        "name": "A",
        "title": "Multiple Choice Questions",
        "types": ("MCQ", "Assertion Reason"),
        "marks_per_question": 1,
        "instructions": "All questions are compulsory. Each question carries 1 mark. Choose the most appropriate option.",
    },
    {
        "name": "B",
        "title": "Very Short Answer Questions",
        "types": ("VSA",),
        "marks_per_question": 2,
        "instructions": "All questions are compulsory. Each question carries 2 marks. Answer in 30-40 words.",
    },
    {
        "name": "C",
        "title": "Short Answer Questions",
        "types": ("SA",),
        "marks_per_question": 3,
        "instructions": "All questions are compulsory. Each question carries 3 marks. Answer in 40-60 words.",
    },
    {
        "name": "D",
        "title": "Case Study Based Questions",
        "types": ("Case Study",),
        "marks_per_question": 4,
        "instructions": "Read the case study carefully and answer the questions that follow. Each question carries 4 marks.",
    },
    {
        "name": "E",
        "title": "Long Answer Questions",
        "types": ("LA",),
        "marks_per_question": 5,
        "instructions": "All questions are compulsory. Each question carries 5 marks. Answer in 70-100 words.",
    },
]


class PaperGenerationOrchestrator:
    """Top-level coordinator for the question-paper generation pipeline."""

    def __init__(
        self,
        weightage_service: WeightageService,
        paper_service: PaperService,
        diagram_service: DiagramService,
        physics_understanding_service: PhysicsUnderstandingService,
        diagram_template_service: DiagramTemplateService,
        schema_population_service: SchemaPopulationService,
        paper_evaluator: PaperEvaluator,
    ) -> None:
        self._weightage_service = weightage_service
        self._paper_service = paper_service
        self._diagram_service = diagram_service
        self._physics_understanding_service = physics_understanding_service
        self._diagram_template_service = diagram_template_service
        self._schema_population_service = schema_population_service
        self._paper_evaluator = paper_evaluator

    def generate_paper(self, request: GeneratePaperRequest) -> GeneratedPaperResponse:
        """Run the full pipeline and return the assembled paper."""

        logger.info(
            "Generating paper: difficulty=%s pyq=%d%% ai=%d%% total_questions=%d "
            "include_diagrams=%s diagram_percentage=%d%% chapters=%s",
            request.difficulty, request.pyq_percentage, request.ai_percentage,
            request.total_questions, request.include_diagrams, request.diagram_percentage, request.chapters,
        )

        scope = self._weightage_service.get_scope_chapters(request.chapters)
        chapter_weightage = self._weightage_service.compute_chapter_weightage(scope)
        logger.info("Chapter weightage: %s", chapter_weightage)

        plan = self._paper_service.generate(request, chapter_weightage)
        logger.info(
            "Paper plan assembled: %d PYQ, %d AI-generated, chapter_distribution=%s, type_distribution=%s",
            len(plan.pyq_questions), len(plan.ai_questions), plan.chapter_distribution, plan.type_distribution,
        )

        diagrams: list[DiagramSpec] = []
        questions = [self._to_question_item(draft, diagrams) for draft in plan.pyq_questions]
        generated_questions = [self._to_question_item(draft, diagrams) for draft in plan.ai_questions]

        sections, numbered_by_id = self._build_sections(questions + generated_questions)
        questions = [numbered_by_id.get(q.question_id, q) for q in questions]
        generated_questions = [numbered_by_id.get(q.question_id, q) for q in generated_questions]

        total_marks = sum(q.marks for q in questions) + sum(q.marks for q in generated_questions)
        total_questions = len(questions) + len(generated_questions)
        diagram_coverage = self._compute_diagram_coverage(questions + generated_questions)

        response = GeneratedPaperResponse(
            paper_id=str(uuid4()),
            generated_at=datetime.now(timezone.utc).isoformat(),
            difficulty=request.difficulty,
            total_questions=total_questions,
            total_marks=total_marks,
            pyq_percentage=request.pyq_percentage,
            ai_percentage=request.ai_percentage,
            chapter_weightage=chapter_weightage,
            chapter_distribution=plan.chapter_distribution,
            type_distribution=plan.type_distribution,
            questions=questions,
            generated_questions=generated_questions,
            diagrams=diagrams,
            diagram_coverage=diagram_coverage,
            sections=sections,
        )

        quality_evaluation = self._paper_evaluator.evaluate(response, chapter_weightage, request)
        response = response.model_copy(update={"quality_evaluation": quality_evaluation})

        logger.info(
            "Paper generation complete: paper_id=%s total_questions=%d total_marks=%d diagrams=%d "
            "diagram_coverage=%.1f%% (%d questions)",
            response.paper_id, response.total_questions, response.total_marks, len(diagrams),
            diagram_coverage.diagram_percentage, diagram_coverage.diagram_questions,
        )
        return response

    def _to_question_item(self, draft: QuestionDraft, diagrams_out: list[DiagramSpec]) -> QuestionItem:
        diagram_id: str | None = None

        if draft.requires_diagram:
            # 1. PhysicsUnderstandingService
            analysis = self._physics_understanding_service.analyze(draft.question)
            
            diagram_type = draft.diagram_type if draft.diagram_type != "none" else analysis.diagram_type
            concept = analysis.concept or draft.concept
            scenario = draft.diagram_scenario or analysis.scenario

            # 2. Template Selection
            template_id, template = self._diagram_template_service.select(diagram_type, concept, scenario)

            # 3. Dynamic Semantic Schema
            semantic_schema = self._schema_population_service.build_semantic_schema(analysis, template_id, template)
            if draft.diagram_entities:
                semantic_schema["required_entities"] = list(set(semantic_schema["required_entities"] + draft.diagram_entities))
            if scenario:
                semantic_schema["scenario"] = scenario
            if diagram_type:
                semantic_schema["diagram_type"] = diagram_type

            # 4. Render Schema
            render_schema = self._schema_population_service.build_render_schema(semantic_schema, draft.question, template)

            # 5. Renderer
            svg = render_svg(render_schema)

            diagram_id = f"DIAG_{draft.question_id}"
            diagrams_out.append(
                DiagramSpec(
                    diagram_id=diagram_id,
                    question_id=draft.question_id,
                    diagram_type=diagram_type,
                    specification=render_schema,
                    svg=svg,
                )
            )

        return QuestionItem(
            question_id=draft.question_id,
            source=draft.source,
            type=draft.type,
            marks=draft.marks,
            chapter=draft.chapter,
            difficulty=draft.difficulty,
            question=draft.question,
            options=draft.options,
            concept=draft.concept,
            requires_diagram=draft.requires_diagram,
            diagram_type=draft.diagram_type,
            diagram_id=diagram_id,
        )

    @staticmethod
    def _build_sections(all_questions: list[QuestionItem]) -> tuple[list[PaperSection], dict[str, QuestionItem]]:
        """Group questions into CBSE Section A-E, numbering them sequentially.

        Returns the assembled sections plus a ``question_id -> numbered
        QuestionItem`` map so the flat ``questions``/``generated_questions``
        lists can carry the same ``question_number`` values.
        """

        sections: list[PaperSection] = []
        numbered_by_id: dict[str, QuestionItem] = {}
        counter = 0

        for section_def in _SECTION_DEFS:
            matching = [q for q in all_questions if q.type in section_def["types"]]
            if not matching:
                continue
            matching.sort(key=lambda q: _DIFFICULTY_ORDER.get(q.difficulty, 1))

            numbered_questions: list[QuestionItem] = []
            for question in matching:
                counter += 1
                numbered = question.model_copy(update={"question_number": counter})
                numbered_questions.append(numbered)
                numbered_by_id[numbered.question_id] = numbered

            sections.append(
                PaperSection(
                    name=section_def["name"],
                    title=section_def["title"],
                    instructions=section_def["instructions"],
                    marks_per_question=section_def["marks_per_question"],
                    question_count=len(numbered_questions),
                    total_marks=sum(q.marks for q in numbered_questions),
                    questions=numbered_questions,
                )
            )

        return sections, numbered_by_id

    @staticmethod
    def _compute_diagram_coverage(questions: list[QuestionItem]) -> DiagramCoverage:
        diagram_questions = [q for q in questions if q.requires_diagram]
        type_counts = {diagram_type: 0 for diagram_type in _TRACKED_DIAGRAM_TYPES}
        for question in diagram_questions:
            if question.diagram_type in type_counts:
                type_counts[question.diagram_type] += 1

        percentage = (len(diagram_questions) / len(questions) * 100) if questions else 0.0

        return DiagramCoverage(
            diagram_questions=len(diagram_questions),
            diagram_percentage=round(percentage, 1),
            **type_counts,
        )
