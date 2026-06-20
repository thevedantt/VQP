"""Chapter Weightage Engine.

Infers chapter importance directly from the PYQ question bank by summing
the marks weight each chapter carries (e.g. a chapter with several
5-mark Long Answer questions is weighted more heavily than one with only
1-mark MCQs), then normalizes to percentages that sum to 100.

Weightage is scoped to chapters covered by the NCERT knowledge base, since
those are the only chapters the AI question generator can be grounded in.
"""

from __future__ import annotations

import logging

from app.core.exceptions import InvalidRequestError
from app.services.allocation import allocate_largest_remainder
from app.services.book_service import BookService
from app.services.question_service import QuestionService

logger = logging.getLogger(__name__)


class WeightageService:
    """Computes chapter weightage percentages from the PYQ dataset."""

    def __init__(self, question_service: QuestionService, book_service: BookService) -> None:
        self._question_service = question_service
        self._book_service = book_service

    def get_scope_chapters(self, requested_chapters: list[str] | None = None) -> list[str]:
        """Return the chapters in scope for paper generation.

        Defaults to every chapter covered by the NCERT knowledge base. If
        ``requested_chapters`` is provided, it is intersected with the
        available chapters (preserving the NCERT chapter ordering).
        """

        available = self._book_service.get_available_chapters()
        if not requested_chapters:
            return available

        available_set = set(available)
        scoped = [c for c in available if c in set(requested_chapters) and c in available_set]
        if not scoped:
            raise InvalidRequestError(
                "None of the requested chapters are available in the NCERT knowledge base.",
                detail=f"requested={requested_chapters}, available={available}",
            )
        return scoped

    def compute_chapter_weightage(self, chapters: list[str] | None = None) -> dict[str, int]:
        """Return chapter -> percentage weightage (sums to 100) for the given scope."""

        scope = chapters if chapters is not None else self.get_scope_chapters()

        marks_by_chapter: dict[str, float] = {chapter: 0.0 for chapter in scope}
        for question in self._question_service.filter(chapters=scope):
            marks_by_chapter[question.chapter] += question.marks

        if sum(marks_by_chapter.values()) == 0:
            logger.warning("No PYQ marks data found for chapters %s; falling back to equal weightage.", scope)
            marks_by_chapter = {chapter: 1.0 for chapter in scope}

        weightage = allocate_largest_remainder(marks_by_chapter, 100)
        logger.debug("Computed chapter weightage: %s", weightage)
        return weightage
