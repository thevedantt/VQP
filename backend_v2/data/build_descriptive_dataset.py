"""
One-time / reproducible builder for backend_v2's descriptive (VSA/SA/LA)
PYQ question pool.

Source: ../backend/app/data/question_bank/labeled_questions.json
    214 deduplicated, chapter/concept-labeled CBSE PYQ entries. This is
    richer than final_dataset.json (which build_pyq_dataset.py reads) -
    it has real chapter tags instead of null, and includes Long Answer
    (LA) questions that build_pyq_dataset.py's TYPE_MAP currently drops.

Text cleanup (Symbol-font decode, scientific-notation superscripting,
paper-instruction artifact stripping) is delegated to
pipeline/normalize_unicode.py - the single source of truth, also used
at selection time.

Run:
    python data/build_descriptive_dataset.py
"""

import hashlib
import json
import sys
from pathlib import Path

BACKEND_V2 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_V2))

from pipeline.normalize_unicode import is_clean, normalize

SOURCE_PATH = (
    BACKEND_V2.parent / "backend" / "app" / "data" / "question_bank" / "labeled_questions.json"
)
OUTPUT_PATH = BACKEND_V2 / "data" / "descriptive_questions.json"

TYPE_MAP = {
    "Very Short Answer (VSA)": "Very Short",
    "Short Answer (SA)": "Short Answer",
    "Long Answer (LA)": "Long Answer",
}


def build():
    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    seen_text = set()
    cleaned = []

    for q in raw:
        canonical_type = TYPE_MAP.get(q.get("type"))
        if not canonical_type:
            continue

        text = normalize((q.get("question") or "").strip())
        if not is_clean(text):
            continue

        norm = " ".join(text.lower().split())
        if norm in seen_text:
            continue
        seen_text.add(norm)

        digest = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:10]

        cleaned.append({
            "pyq_id": f"PYQ_{digest}",
            "question": text,
            "type": canonical_type,
            "marks": q.get("marks"),
            "chapter": q.get("chapter"),
            "concept": q.get("concept"),
            "difficulty": q.get("difficulty"),
            "options": q.get("options") or None,
            "diagram_required": bool(q.get("requires_diagram")),
            "source_file": q.get("source_file"),
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(cleaned)} descriptive PYQ questions to {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
