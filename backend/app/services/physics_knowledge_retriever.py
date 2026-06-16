"""NCERT knowledge retrieval for the Dynamic Physics Semantic Schema pipeline.

Sits between Phase 1 (concept/chapter detection) and the LLM call:

    Question -> concept/chapter detection -> PhysicsKnowledgeRetriever -> LLM

Grounds the physics-analysis prompt in the actual NCERT textbook content
(``BookService``) instead of letting the LLM rely on the question text alone.
Returns a plain, JSON-serializable dict - safe to embed directly in prompts
and in the ``PhysicsAnalysis.textbook_context`` field exposed to the
playground.
"""

from __future__ import annotations

import re

from app.models.enums import DiagramType
from app.services.book_service import BookService
from app.services.diagram_taxonomy_service import DiagramTaxonomyService

# Sentences containing these words are prioritized when extracting
# "important_points" from a retrieved excerpt - they tend to describe the
# diagram/figure itself rather than surrounding derivations.
_DIAGRAM_SENTENCE_HINTS = ["figure", "fig.", "shown", "shows", "direction", "field line", "diagram"]

_EMPTY_CONTEXT: dict = {
    "chapter": "",
    "topic": "",
    "description": "",
    "diagram_explanation": "",
    "expected_labels": [],
    "important_points": [],
}


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


class PhysicsKnowledgeRetriever:
    """Retrieves grounding NCERT content for a detected chapter/concept."""

    def __init__(self, book_service: BookService, taxonomy_service: DiagramTaxonomyService) -> None:
        self._book_service = book_service
        self._taxonomy_service = taxonomy_service

    def retrieve(
        self,
        chapter: str | None,
        diagram_type: DiagramType,
        concept: str | None,
        scenario: str | None,
    ) -> dict:
        """Return NCERT grounding context for the given chapter/concept.

        Returns an empty-but-valid context (all fields present, but empty) if
        the chapter is unknown or not yet ingested into the knowledge base -
        e.g. NCERT Part 2 chapters (Ray Optics, etc.) are not yet ingested.
        """

        if not chapter or not self._book_service.has_chapter(chapter):
            return dict(_EMPTY_CONTEXT)

        excerpt = self._book_service.get_excerpt(chapter, concept=concept, max_chars=1500)

        expected_labels: list[str] = []
        if diagram_type != "none" and concept:
            concept_entry = self._taxonomy_service.get_concept_entry(diagram_type, concept)
            if concept_entry:
                expected_labels = list(concept_entry.get("entities", []))

        return {
            "chapter": chapter,
            "topic": concept or scenario or "",
            "description": excerpt,
            "diagram_explanation": excerpt,
            "expected_labels": expected_labels,
            "important_points": self._important_points(excerpt, concept),
        }

    @staticmethod
    def _important_points(excerpt: str, concept: str | None, limit: int = 5) -> list[str]:
        """Pick the most diagram-relevant sentences from an excerpt."""

        sentences = _split_sentences(excerpt)
        if not sentences:
            return []

        concept_words = [w for w in re.findall(r"[a-zA-Z]+", (concept or "").lower()) if len(w) > 2]

        def score(sentence: str) -> int:
            lower = sentence.lower()
            return sum(lower.count(hint) for hint in _DIAGRAM_SENTENCE_HINTS) + sum(
                lower.count(word) for word in concept_words
            )

        ranked = sorted(sentences, key=score, reverse=True)
        top = [s for s in ranked if score(s) > 0][:limit]
        if top:
            return top
        return sentences[:limit]
