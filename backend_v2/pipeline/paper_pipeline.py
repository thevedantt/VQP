"""
Paper-level orchestration on top of diagram_pipeline.generate_diagram.

For every question in a paper:
    Classifier -> (if diagram required) -> generate_diagram -> store path
                -> (else) -> skip

Produces:
    - outputv2/paper_outputs/{paper_id}.json
    - outputv2/compiled_svgs/{paper_id}_{question_id}.svg (per diagram)
    - outputv2/logs/<timestamp>.log
    - a terminal report

Usage:
    python pipeline/paper_pipeline.py
"""

import json
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
BACKEND_V2 = PIPELINE_DIR.parent

sys.path.insert(0, str(BACKEND_V2))
sys.path.insert(0, str(BACKEND_V2.parent))

from pipeline.logger import PipelineLogger
from pipeline.diagram_pipeline import generate_diagram, get_components


OUTPUTV2_DIR = BACKEND_V2 / "outputv2"
PAPER_OUTPUT_DIR = OUTPUTV2_DIR / "paper_outputs"
PAPER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_paper(paper_id, questions, logger=None):
    own_logger = logger is None
    if own_logger:
        logger = PipelineLogger()

    classifier, _, _ = get_components()

    output_questions = []
    diagram_count = 0
    generated_count = 0
    failed_count = 0

    try:
        for q in questions:
            qid = q["question_id"]
            question_text = q["question"]

            row = {
                "question_id": qid,
                "question": question_text,
                "family": None,
                "diagram_required": False,
                "diagram_path": None,
                "status": "SKIPPED",
                "error": None,
            }

            try:
                classification = classifier.classify(question_text)
                logger.log_classifier(question_text, classification)

                if not classification.get("diagram_required"):
                    output_questions.append(row)
                    continue

                diagram_count += 1
                row["diagram_required"] = True

                diagram_result = generate_diagram(
                    question_text,
                    paper_id=paper_id,
                    question_id=qid,
                    logger=logger,
                    classification=classification,
                )

                row["family"] = diagram_result.get("family")

                if diagram_result["status"] == "SUCCESS":
                    row["status"] = "SUCCESS"
                    row["diagram_path"] = diagram_result["svg_path"]
                    generated_count += 1
                else:
                    row["status"] = "FAILED"
                    row["error"] = diagram_result.get("error")
                    failed_count += 1

            except Exception as e:
                row["status"] = "FAILED"
                row["error"] = str(e)
                failed_count += 1
                logger.log_error("PAPER PIPELINE", f"{qid}: {e}")

            output_questions.append(row)

        paper_output = {
            "paper_id": paper_id,
            "questions": output_questions,
        }

        output_path = PAPER_OUTPUT_DIR / f"{paper_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(paper_output, f, indent=2, ensure_ascii=False)

        logger.log_paper_pipeline(len(questions), diagram_count, str(output_path))

        summary = {
            "total": len(questions),
            "diagram_questions": diagram_count,
            "generated": generated_count,
            "failed": failed_count,
        }

        _print_report(paper_id, output_questions, summary)

        return {
            "paper_id": paper_id,
            "output_path": str(output_path),
            "questions": output_questions,
            "summary": summary,
        }

    finally:
        if own_logger:
            logger.close()


def _print_report(paper_id, rows, summary):
    print()
    print("=" * 60)
    print("PAPER GENERATION REPORT")
    print("=" * 60)
    print()
    print(f"Paper ID : {paper_id}")

    for row in rows:
        print()
        print("---")
        print()
        print(row["question_id"])
        print()
        print("Question:")
        print(row["question"])
        print()

        if row["diagram_required"]:
            print("Family:")
            print(row.get("family") or "N/A")
            print()
            print("Diagram:")
            print("YES")
            print()
            if row.get("diagram_path"):
                print("SVG:")
                print(row["diagram_path"])
                print()
        else:
            print("Diagram:")
            print("NO")
            print()

        print("Status:")
        print(row["status"])

        if row.get("error"):
            print()
            print("Error:")
            print(row["error"])

    print()
    print("=" * 60)
    print()
    print("SUMMARY")
    print()
    print(f"Questions: {summary['total']}")
    print(f"Diagram Questions: {summary['diagram_questions']}")
    print(f"Generated: {summary['generated']}")
    print(f"Failed: {summary['failed']}")
    print()
    print("=" * 60)


SAMPLE_QUESTIONS = [
    {
        "question_id": "Q01",
        "question": "Draw a ray diagram for an object placed between F1 and 2F1 of a convex lens.",
    },
    {
        "question_id": "Q02",
        "question": "State Ohm's Law.",
    },
    {
        "question_id": "Q03",
        "question": "Draw a free body diagram of a block resting on a rough horizontal surface.",
    },
]


def main():
    result = generate_paper("PAPER001", SAMPLE_QUESTIONS)

    from pipeline.pdf_export import export_paper_to_pdf

    pdf_path = export_paper_to_pdf(result["output_path"])
    print()
    print(f"PDF: {pdf_path}")


if __name__ == "__main__":
    main()
