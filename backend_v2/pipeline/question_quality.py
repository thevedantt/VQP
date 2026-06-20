"""
Question quality scoring (Phase 3B Task 7) - 0-100, stored as
`quality_score` in each question's metadata.

Five factors, weighted to sum to 100:
    Completeness     25  - has real content, not a truncated fragment,
                            MCQs have usable distinct options
    Formatting        20  - no leftover layout artifacts (stray blank
                            lines, dangling connector words)
    Unicode Quality   20  - no unmapped Private-Use-Area glyphs left
    Marks Match       20  - PYQ marks are exam-verified (full score);
                            AI marks are checked against an expected
                            word-count range for that mark value
    Concept Clarity   15  - chapter/concept tags present (PYQ has them;
                            AI questions are scored down since they're
                            untagged)
"""

import re

from pipeline.normalize_unicode import is_clean

_DANGLING_CONNECTORS = re.compile(r"(?:\bOR\b|\(a\)|\(b\)|\(i\)|\(ii\))\s*$", re.IGNORECASE)

# Rough expected word-count band per mark value, used only to sanity-check
# AI-generated questions (PYQ marks are already exam-verified).
_EXPECTED_WORDS_BY_MARKS = {
    1: (4, 40),
    2: (8, 60),
    3: (12, 90),
    4: (20, 140),
    5: (25, 180),
    6: (30, 200),
}


def _score_completeness(question):
    text = (question.get("question") or "").strip()
    score = 25

    if len(text) < 15:
        score -= 15
    if _DANGLING_CONNECTORS.search(text):
        score -= 10

    if question.get("type") == "MCQ":
        options = question.get("options") or {}
        values = [str(v).strip() for v in options.values() if str(v).strip()]
        if len(values) < 4:
            score -= 10
        elif len(set(values)) != len(values):
            score -= 10

    return max(0, score)


def _score_formatting(question):
    text = question.get("question") or ""
    score = 20

    if re.search(r"\n{4,}", text):
        score -= 5
    if text != text.strip():
        score -= 3
    if re.search(r"\s{3,}", text):
        score -= 3

    return max(0, score)


def _score_unicode_quality(question):
    text = question.get("question") or ""
    options = question.get("options") or {}

    if not is_clean(text):
        return 0
    for value in options.values():
        if not is_clean(str(value)):
            return 5

    return 20


def _score_marks_match(question):
    if question.get("source") == "PYQ":
        return 20

    marks = question.get("marks")
    word_count = len((question.get("question") or "").split())
    bounds = _EXPECTED_WORDS_BY_MARKS.get(marks)

    if not bounds:
        return 12  # unknown mark value - can't validate, partial credit

    low, high = bounds
    if low <= word_count <= high:
        return 20
    if word_count < low:
        return 10  # likely too terse for the mark value
    return 14  # likely too verbose, less harmful than too terse


def _score_concept_clarity(question):
    has_chapter = bool(question.get("chapter"))
    has_concept = bool(question.get("concept"))

    if has_chapter and has_concept:
        return 15
    if has_chapter or has_concept:
        return 8
    return 3


def score_question(question):
    """Returns an int 0-100 quality score for one selected question row."""
    return (
        _score_completeness(question)
        + _score_formatting(question)
        + _score_unicode_quality(question)
        + _score_marks_match(question)
        + _score_concept_clarity(question)
    )
