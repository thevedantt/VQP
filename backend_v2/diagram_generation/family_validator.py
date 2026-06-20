"""
Family Validator (Phase 4.1, Task 4).

Prevents the classifier from assigning a wrong family to a question.
Uses keyword-based heuristics keyed to each family's distinctive vocabulary
to catch clear mismatches (e.g. a "pn junction" question classified as
"ray" or a "convex lens" question classified as "circuit").

If the validation fails, the pipeline aborts generation and logs the error.
"""

import re
import sys
from pathlib import Path

BACKEND_V2 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_V2))

from pipeline.diagram_detector import FAMILY_KEYWORDS


# Each family's strongly-associated keyword set (drawn from the detector
# vocabulary). Questions matching these keywords STRONGLY suggest the
# corresponding family.
EXPECTED_KEYWORDS = {
    family: {kw.lower() for kw in keywords}
    for family, keywords in FAMILY_KEYWORDS
}

# For each family, list of families that are NEVER valid for questions
# whose keyword signature strongly suggests this family.
# E.g. if question mentions "pn junction" it MUST be semiconductor or
# circuit — never ray.
CONFLICT_MATRIX = {
    "fbd": {"ray", "circuit", "magnetic", "semiconductor", "graph"},
    "ray": {"circuit", "fbd", "magnetic", "semiconductor", "graph"},
    "circuit": {"ray", "fbd", "magnetic", "graph"},
    "magnetic": {"ray", "circuit", "fbd", "graph"},
    # "circuit" is NEVER valid when the question strongly suggests
    # semiconductor (diode, PN junction, bias, transistor, LED,
    # photodiode, solar cell) - those are nonlinear semiconductor
    # devices, not basic circuit components (Phase 4.8, Issue 2).
    "semiconductor": {"ray", "fbd", "magnetic", "graph", "circuit"},
    "graph": {"ray", "circuit", "fbd", "magnetic", "semiconductor"},
}

_WORD_RE = re.compile(r"[a-z0-9']+")


def _tokenize(text):
    return {m.group() for m in _WORD_RE.finditer((text or "").lower())}


def _strongly_suggests(text):
    """
    Returns the family most strongly suggested by the question text, or None.
    The family with the most keyword hits wins.
    """
    words = _tokenize(text)
    scores = {}

    for family, keywords in EXPECTED_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text.lower())
        if matches > 0:
            scores[family] = matches

    if not scores:
        return None

    return max(scores, key=scores.get)


def validate(question, classified_family):
    """
    Validate that the classified family is compatible with the question text.

    Returns:
        {
            "valid": True/False,
            "expected_family": str | None,
            "classified_family": str,
            "reason": str | None,
        }
    """
    if not question or not classified_family:
        return {
            "valid": True,
            "expected_family": None,
            "classified_family": classified_family,
            "reason": None,
        }

    suggested = _strongly_suggests(question)

    if suggested is None:
        return {
            "valid": True,
            "expected_family": None,
            "classified_family": classified_family,
            "reason": "No strong family signal in question text",
        }

    conflict_set = CONFLICT_MATRIX.get(suggested, set())

    if classified_family in conflict_set:
        return {
            "valid": False,
            "expected_family": suggested,
            "classified_family": classified_family,
            "reason": (
                f"Question strongly suggests '{suggested}' but classifier "
                f"returned '{classified_family}'. "
                f"'{suggested}' keywords found in question text."
            ),
        }

    return {
        "valid": True,
        "expected_family": suggested,
        "classified_family": classified_family,
        "reason": None,
    }


def main():
    question = input("Question: ")
    family = input("Classified family: ")

    result = validate(question, family)

    print()
    print(f"Valid: {result['valid']}")
    print(f"Expected family: {result['expected_family']}")
    print(f"Classified family: {result['classified_family']}")
    if result["reason"]:
        print(f"Reason: {result['reason']}")


if __name__ == "__main__":
    main()
