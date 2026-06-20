"""
Paper Generation Engine (Phase 3B): template -> selected questions ->
locked question list -> quality scoring -> JSON -> terminal reports.

Diagram generation is explicitly out of scope for this phase - no
classifier, schema_router, blueprint_generator, blueprint_evaluator, or
compiler_router is touched here. The only diagram-related output is the
detected `diagram_required` / `diagram_family` already carried by each
question.

Usage:
    python pipeline/paper_builder.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
BACKEND_V2 = PIPELINE_DIR.parent

sys.path.insert(0, str(BACKEND_V2))

from pipeline.logger import PipelineLogger
from pipeline.paper_templates import get_template
from pipeline.question_quality import score_question
from pipeline.question_selector import QuestionSelector


OUTPUTV2_DIR = BACKEND_V2 / "outputv2"
PAPERS_DIR = OUTPUTV2_DIR / "papers"
PAPERS_DIR.mkdir(parents=True, exist_ok=True)


def build_paper(
    paper_id,
    template_name,
    pyq_ratio=60,
    ai_ratio=40,
    chapter_filters=None,
    difficulty=None,
    overall_diagram_ratio=0.2,
    logger=None,
):
    own_logger = logger is None
    if own_logger:
        logger = PipelineLogger()

    try:
        template = get_template(template_name)

        selector = QuestionSelector(
            pyq_ratio=pyq_ratio,
            ai_ratio=ai_ratio,
            chapter_filters=chapter_filters,
            difficulty=difficulty,
            logger=logger,
        )

        # ---- Select PYQ + AI questions, enforce diagram quotas (detection only) ----
        rows = selector.select_for_template(template)
        rows = selector.enforce_overall_diagram_ratio(rows, target_ratio=overall_diagram_ratio)
        # Final paper-wide correction: per-block selection only targets a
        # per-block ratio, which drifts from the configured PYQ/AI split
        # (rounding, diagram-quota AI fallbacks). This recomputes the
        # quota from the final question count and corrects the actual
        # paper to match it exactly, before anything is finalized.
        rows = selector.enforce_overall_pyq_ratio(rows)

        # ---- Lock the question list ----
        for idx, row in enumerate(rows, start=1):
            row["question_id"] = f"Q{idx:02d}"

        questions = []
        for row in rows:
            question = {
                "question_id": row["question_id"],
                "question": row["question"],
                "source": row["source"],
                "type": row["type"],
                "section_id": row["section_id"],
                "marks": row["marks"],
                "options": row.get("options"),
                "diagram_required": row["diagram_required"],
                "diagram_family": row.get("diagram_family"),
                "chapter": row.get("chapter"),
                "concept": row.get("concept"),
            }
            question["quality_score"] = score_question(question)
            questions.append(question)

        # ---- Build & save final paper JSON ----
        diagram_questions = [q for q in questions if q["diagram_required"]]
        chapter_distribution = Counter(q["chapter"] for q in questions if q["chapter"])
        diagram_family_counts = Counter(q["diagram_family"] for q in diagram_questions if q["diagram_family"])
        avg_quality = (
            round(sum(q["quality_score"] for q in questions) / len(questions), 1)
            if questions else 0.0
        )

        total_questions = len(questions)
        pyq_questions = sum(1 for q in questions if q["source"] == "PYQ")
        ai_questions = sum(1 for q in questions if q["source"] == "AI")

        summary = {
            "total_questions": total_questions,
            "pyq_questions": pyq_questions,
            "ai_questions": ai_questions,
            "diagram_questions": len(diagram_questions),
            "chapter_distribution": dict(chapter_distribution),
            "diagram_family_counts": dict(diagram_family_counts),
            "average_quality_score": avg_quality,
            # Configured vs. actual PYQ/AI split (Phase: PYQ/AI split
            # accuracy fix) - computed from real counts, never just
            # echoed back from the requested ratio.
            "configured_pyq_ratio": round(selector.pyq_ratio, 4),
            "configured_ai_ratio": round(selector.ai_ratio, 4),
            "actual_pyq_ratio": (
                round(pyq_questions / total_questions, 4) if total_questions else 0.0
            ),
            "actual_ai_ratio": (
                round(ai_questions / total_questions, 4) if total_questions else 0.0
            ),
        }

        paper_output = {
            "paper_id": paper_id,
            "paper_type": template_name,
            "total_marks": template["total_marks"],
            "pyq_ratio": selector.pyq_ratio,
            "ai_ratio": selector.ai_ratio,
            "questions": questions,
            "summary": summary,
        }

        output_path = PAPERS_DIR / f"{paper_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(paper_output, f, indent=2, ensure_ascii=False)

        logger.log_paper_pipeline(len(questions), summary["diagram_questions"], str(output_path))

        _print_question_report(paper_id, questions, summary)
        _print_selection_report(summary)

        return paper_output, str(output_path)

    finally:
        if own_logger:
            logger.close()


def _print_question_report(paper_id, questions, summary):
    print()
    print("=" * 60)
    print("PAPER GENERATION REPORT")
    print("=" * 60)
    print()
    print("Paper ID:")
    print(paper_id)

    for q in questions:
        print()
        print("---")
        print()
        print(q["question_id"])
        print()
        print("Source:")
        print(q["source"])
        print()
        print("Marks:")
        print(q["marks"])
        print()
        print("Diagram:")
        print("YES" if q["diagram_required"] else "NO")

    print()
    print("---")
    print()
    print("SUMMARY")
    print()
    print(f"Questions: {summary['total_questions']}")
    print(f"PYQ Questions: {summary['pyq_questions']}")
    print(f"AI Questions: {summary['ai_questions']}")
    print(f"Diagram Questions (detected): {summary['diagram_questions']}")
    print()
    print(
        f"Configured Split: {summary['configured_pyq_ratio'] * 100:.1f}% / "
        f"{summary['configured_ai_ratio'] * 100:.1f}%"
    )
    print(
        f"Actual Split:     {summary['actual_pyq_ratio'] * 100:.1f}% / "
        f"{summary['actual_ai_ratio'] * 100:.1f}%"
    )
    print()
    print("=" * 60)


def _print_selection_report(summary):
    print()
    print("=" * 60)
    print()
    print("QUESTION SELECTION REPORT")
    print()
    print("=" * 60)
    print()
    print(f"Questions Selected: {summary['total_questions']}")
    print()
    print(f"PYQ Questions: {summary['pyq_questions']}")
    print(f"AI Questions: {summary['ai_questions']}")
    print()
    print(
        f"Configured Split: {summary['configured_pyq_ratio'] * 100:.1f}% / "
        f"{summary['configured_ai_ratio'] * 100:.1f}%"
    )
    print(
        f"Actual Split:     {summary['actual_pyq_ratio'] * 100:.1f}% / "
        f"{summary['actual_ai_ratio'] * 100:.1f}%"
    )
    print()
    print("---")
    print()
    print("Chapter Distribution")
    print()
    for chapter, count in summary["chapter_distribution"].items():
        print(f"{chapter}: {count}")
    print()
    print("---")
    print()
    print("Diagram Questions")
    print()
    for family, count in summary["diagram_family_counts"].items():
        print(f"{family.capitalize()}: {count}")
    print()
    print("---")
    print()
    print("Average Quality Score")
    print()
    print(summary["average_quality_score"])
    print()
    print("=" * 60)


def main():
    paper_id = "PAPER001"
    template_name = "UNIT_TEST_20"

    build_paper(paper_id, template_name)


if __name__ == "__main__":
    main()
