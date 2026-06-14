"""Export helpers for serializing a generated paper into other formats.

Currently provides plain JSON (dict) and a human-readable plain-text
rendering suitable for previewing a paper or as a starting point for a
future PDF export pipeline.
"""

from __future__ import annotations

from typing import Any

from app.models.responses import GeneratedPaperResponse, QuestionItem


class ExportService:
    """Serializes a GeneratedPaperResponse into alternative formats."""

    @staticmethod
    def to_dict(paper: GeneratedPaperResponse) -> dict[str, Any]:
        """Return the paper as a plain JSON-serializable dict."""

        return paper.model_dump()

    @staticmethod
    def to_text(paper: GeneratedPaperResponse) -> str:
        """Render the paper as a plain-text CBSE-style question sheet."""

        lines: list[str] = [
            "VisualQ Pilot - CBSE Physics Unit Test",
            f"Difficulty: {paper.difficulty.title()} | "
            f"Total Questions: {paper.total_questions} | Total Marks: {paper.total_marks}",
            "=" * 60,
        ]

        all_questions: list[QuestionItem] = [*paper.questions, *paper.generated_questions]
        for index, item in enumerate(all_questions, start=1):
            lines.append("")
            lines.append(f"Q{index}. [{item.type} | {item.marks} mark(s) | {item.chapter}]")
            lines.append(item.question.strip())
            for key, value in item.options.items():
                lines.append(f"   ({key}) {value.strip()}")
            if item.requires_diagram:
                lines.append(f"   [Diagram required: {item.diagram_type}]")

        if paper.diagrams:
            lines.append("")
            lines.append("-" * 60)
            lines.append(f"Diagram specifications generated: {len(paper.diagrams)}")
            for diagram in paper.diagrams:
                lines.append(f"  - {diagram.diagram_id} ({diagram.diagram_type}) for {diagram.question_id}")

        return "\n".join(lines)
