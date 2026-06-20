"""
Diagram scanner (Phase 4, Module 1).

Scans an already-generated paper.json and identifies every question that
requires a diagram. Detection itself already happened in
pipeline/paper_builder.py (diagram_required / diagram_family per question) -
this module just reads that result back off disk for the diagram generation
pipeline to consume.
"""

import json
from pathlib import Path


BACKEND_V2 = Path(__file__).resolve().parent.parent
PAPERS_DIR = BACKEND_V2 / "outputv2" / "papers"


def load_paper(paper_id):
    paper_path = PAPERS_DIR / f"{paper_id}.json"

    if not paper_path.exists():
        raise FileNotFoundError(f"Paper not found: {paper_id}")

    with open(paper_path, "r", encoding="utf-8") as f:
        return json.load(f)


def scan_paper(paper_id):
    """
    Returns:
        {
            "paper_id": "PAPER001",
            "diagram_questions": [
                {"question_id": "Q07", "family": "ray", "question": "..."},
                ...
            ],
        }

    `family` is the paper-builder's keyword heuristic - a hint only. The
    diagram generation pipeline re-classifies each question with the real
    LLM classifier before trusting a family.
    """
    paper = load_paper(paper_id)

    diagram_questions = [
        {
            "question_id": q["question_id"],
            "family": q.get("diagram_family"),
            "question": q["question"],
        }
        for q in paper.get("questions", [])
        if q.get("diagram_required")
    ]

    return {
        "paper_id": paper_id,
        "diagram_questions": diagram_questions,
    }


def main():
    paper_id = input("Paper ID: ")

    result = scan_paper(paper_id)

    print()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
