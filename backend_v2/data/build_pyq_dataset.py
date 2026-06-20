"""
One-time / reproducible builder for backend_v2's PYQ question pool.

Source: ../../archive/backend/app/data/question_bank/final_dataset.json
    267 raw CBSE PYQ entries scraped from past papers. ~40% are
    non-English / garbled PDF-extraction artifacts (private-use-area
    glyphs from a broken font mapping) and are dropped here. The
    source dataset has no Long Answer (5-6 mark) questions and no
    chapter tags, so those gaps are filled by AI generation at
    selection time.

Run:
    python data/build_pyq_dataset.py
"""

import hashlib
import json
from pathlib import Path

BACKEND_V2 = Path(__file__).resolve().parent.parent
SOURCE_PATH = (
    BACKEND_V2.parent / "archive" / "backend" / "app" / "data" / "question_bank" / "final_dataset.json"
)
OUTPUT_PATH = BACKEND_V2 / "data" / "pyq_questions.json"

TYPE_MAP = {
    "MCQ": "MCQ",
    "Very Short Answer (VSA)": "Very Short",
    "Short Answer (SA)": "Short Answer",
    "Assertion Reason": "Assertion Reason",
    "Case Study": "Case Study",
}


def _is_clean(text):
    return bool(text) and all(ord(c) < 128 for c in text)


def _strip_non_ascii(text):
    """Drop trailing PDF-extraction artifacts (private-use-area glyphs)."""
    return "".join(c for c in text if ord(c) < 128).strip()


def _clean_options(options):
    if not options:
        return None

    cleaned = {}
    for key, value in options.items():
        value = _strip_non_ascii(str(value).strip())
        if not value:
            return None  # an option went fully non-ASCII - reject the whole question
        cleaned[key] = value
    return cleaned


def build():
    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    seen_text = set()
    cleaned = []

    for q in raw:
        text = (q.get("question") or "").strip()
        if not _is_clean(text):
            continue

        canonical_type = TYPE_MAP.get(q.get("type"))
        if not canonical_type:
            continue

        raw_options = q.get("options") or None
        if raw_options:
            cleaned_options = _clean_options(raw_options)
            if cleaned_options is None:
                continue  # options too garbled to use
        else:
            cleaned_options = None

        norm = " ".join(text.lower().split())
        if norm in seen_text:
            continue
        seen_text.add(norm)

        # Content-derived, not positional, so the id is stable across
        # rebuilds even if filtering drops/admits a different set of
        # entries - the classification cache keys on this id.
        digest = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:10]

        cleaned.append({
            "pyq_id": f"PYQ_{digest}",
            "question": text,
            "type": canonical_type,
            "marks": q.get("marks"),
            "chapter": q.get("chapter"),
            "options": cleaned_options,
            "source_file": q.get("source_file"),
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(cleaned)} cleaned PYQ questions to {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
