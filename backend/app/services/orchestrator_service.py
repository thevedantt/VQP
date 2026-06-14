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
from app.models.responses import DiagramCoverage, DiagramSpec, GeneratedPaperResponse, QuestionItem
from app.services.diagram_service import DiagramService
from app.services.paper_service import PaperService, QuestionDraft
from app.services.weightage_service import WeightageService

logger = logging.getLogger(__name__)

# Diagram types tracked individually in the DiagramCoverage analytics.
_TRACKED_DIAGRAM_TYPES = ("free_body", "circuit", "ray_diagram", "graph", "magnetic_field")


class PaperGenerationOrchestrator:
    """Top-level coordinator for the question-paper generation pipeline."""

    def __init__(
        self,
        weightage_service: WeightageService,
        paper_service: PaperService,
        diagram_service: DiagramService,
    ) -> None:
        self._weightage_service = weightage_service
        self._paper_service = paper_service
        self._diagram_service = diagram_service

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
        )

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
            diagram = self._diagram_service.build_diagram(draft.diagram_type, draft.question)
            diagram_id = f"DIAG_{draft.question_id}"
            diagrams_out.append(
                DiagramSpec(
                    diagram_id=diagram_id,
                    question_id=draft.question_id,
                    diagram_type=diagram["diagram_type"],
                    specification=diagram["specification"],
                    svg=diagram["svg"],
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
