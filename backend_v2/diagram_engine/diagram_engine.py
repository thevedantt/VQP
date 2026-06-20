"""
Unified public API for the VisualQ diagram engine (Phase 4.4).

Usage:

    from diagram_engine import DiagramEngine

    engine = DiagramEngine()
    result = engine.generate_diagram(
        question="A circuit consists of...",
        question_id="Q07",
        paper_id="PAPER001",
    )
    # => {"question_id": "Q07", "status": "SUCCESS", "family": "circuit",
    #     "svg_path": "...", "reason": "...", "generation_time": 11.2,
    #     "error": None, ...}
"""

from diagram_engine.diagram_service import run as _run_service


class DiagramEngine:

    def generate_diagram(self, question, question_id, paper_id):
        """
        Generate a diagram for a single question.

        Args:
            question:   Question text.
            question_id:  e.g. "Q07"
            paper_id:   e.g. "PAPER001"

        Returns:
            dict with keys:
                question_id (str | None)
                status ("SUCCESS" | "SKIPPED" | "FAILED")
                family (str | None)
                svg_path (str | None) — absolute filesystem path to SVG
                reason (str | None) — explanation
                similarity_score (float | None)
                generation_mode ("EXAMPLE_BASED" | "SCHEMA_BASED" | None)
                confidence (int | None)
                generation_time (float | None) — seconds
                error (str | None)
        """
        return _run_service(
            question=question,
            paper_id=paper_id,
            question_id=question_id,
        )
