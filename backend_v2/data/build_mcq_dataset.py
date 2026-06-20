"""
One-time / reproducible builder for backend_v2's MCQ PYQ question pool,
in the same enriched schema as descriptive_questions.json (chapter,
concept, difficulty populated from labeling instead of null) so the
question selector can filter/match MCQs the same way it would for
descriptive types.

Source: ../backend/app/data/question_bank/labeled_questions.json
    214 deduplicated, chapter/concept-labeled CBSE PYQ entries.

Some MCQ entries are Hindi-language duplicates of an English MCQ
elsewhere in the same source (CBSE bilingual papers print both per
question); their text survived as Devanagari Private-Use-Area glyphs
that have no recoverable mapping here, so they're dropped - the clean
English counterpart is already present as its own entry.

Text cleanup (Symbol-font decode, scientific-notation superscripting,
paper-instruction artifact stripping) is delegated to
pipeline/normalize_unicode.py - the single source of truth, also used
at selection time.

Run:
    python data/build_mcq_dataset.py
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
OUTPUT_PATH = BACKEND_V2 / "data" / "mcq_questions.json"

TYPE_MAP = {
    "MCQ": "MCQ",
}


def _clean_options(options):
    if not options:
        return None

    cleaned = {}
    for key, value in options.items():
        value = normalize(str(value).strip())
        if not is_clean(value):
            return None
        cleaned[key] = value

    # Subscripts are lost in plain-text extraction for a handful of
    # questions (e.g. q1/m1 vs q2/m2 comparisons), leaving two or more
    # options textually identical after decoding - such a question can't
    # be displayed unambiguously, so reject the whole thing.
    if len(set(cleaned.values())) != len(cleaned):
        return None

    return cleaned


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

        cleaned_options = _clean_options(q.get("options"))
        if not cleaned_options:
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
            "options": cleaned_options,
            "diagram_required": bool(q.get("requires_diagram")),
            "source_file": q.get("source_file"),
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(cleaned)} MCQ PYQ questions to {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
