"""
Example retriever (Phase 4, Module 3).

Finds the closest matching example blueprint for a question, within a
family's example library (schemas/{family}/examples.json). The example
library is the source of truth for diagram generation - this module never
invents a blueprint, it only ranks existing examples.

Similarity is a blend of three stdlib-only signals (no embedding model is
installed in this project, and the example pools are tiny - a handful of
entries per family - so a heavier dependency isn't warranted):

    - sentence similarity: difflib.SequenceMatcher ratio over the raw text
    - keyword similarity:  Jaccard over lowercased word sets
    - concept similarity:  Jaccard over the family's physics-keyword
      vocabulary already defined in pipeline/diagram_detector.py
"""

import difflib
import re
import sys
from pathlib import Path

BACKEND_V2 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_V2))

from diagram_intelligence.router.schema_router import SchemaRouter
from pipeline.diagram_detector import FAMILY_KEYWORDS


_FAMILY_CONCEPT_WORDS = {family: set(keywords) for family, keywords in FAMILY_KEYWORDS}

_STOPWORDS = {
    "a", "an", "the", "is", "are", "of", "in", "on", "for", "to", "and",
    "or", "with", "at", "by", "from", "this", "that", "what", "find",
    "draw", "show", "given", "if", "as", "be", "was", "were", "it", "its",
}

_WORD_RE = re.compile(r"[a-z0-9']+")


def _tokenize(text):
    words = _WORD_RE.findall((text or "").lower())
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}


def _jaccard(set_a, set_b):
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def _example_text(example):
    """
    Only the `ray` family's examples are wrapped as {"question", "blueprint"}.
    The other five families' examples.json entries are bare blueprint dicts
    with no natural-language question - build a text proxy out of their
    descriptive fields (object_type, diagram_type, component/force labels)
    so similarity scoring still has something lexical to compare against.
    """
    if isinstance(example.get("question"), str):
        return example["question"]

    parts = []

    for key in ("diagram_family", "diagram_type", "circuit_type", "object_type"):
        value = example.get(key)
        if isinstance(value, str):
            parts.append(value.replace("_", " "))

    for component in example.get("components") or []:
        if isinstance(component, dict) and isinstance(component.get("type"), str):
            parts.append(component["type"].replace("_", " "))

    for force in example.get("forces") or []:
        if isinstance(force, dict) and isinstance(force.get("label"), str):
            parts.append(force["label"].replace("_", " "))

    return " ".join(parts)


def _sentence_similarity(question, example_question):
    return difflib.SequenceMatcher(
        None, (question or "").lower(), (example_question or "").lower()
    ).ratio()


def _keyword_similarity(question, example_question):
    return _jaccard(_tokenize(question), _tokenize(example_question))


def _concept_similarity(question, example_question, family):
    vocab = _FAMILY_CONCEPT_WORDS.get((family or "").lower().strip())
    if not vocab:
        return 0.0

    lowered_q = (question or "").lower()
    lowered_ex = (example_question or "").lower()

    concepts_q = {kw for kw in vocab if kw in lowered_q}
    concepts_ex = {kw for kw in vocab if kw in lowered_ex}

    return _jaccard(concepts_q, concepts_ex)


def score_example(question, example, family):
    example_question = _example_text(example)

    sentence_score = _sentence_similarity(question, example_question)
    keyword_score = _keyword_similarity(question, example_question)
    concept_score = _concept_similarity(question, example_question, family)

    return (0.4 * sentence_score) + (0.35 * keyword_score) + (0.25 * concept_score)


def retrieve(question, family):
    """
    Returns:
        {"best_match": {...example...}, "similarity_score": 0.94}

    Raises ValueError if the family has no examples (SchemaRouter already
    guarantees examples.json exists, but it could be an empty list).
    """
    assets = SchemaRouter().get_family_assets(family)
    examples = assets["examples"]

    if not examples:
        raise ValueError(f"No examples available for family: {family}")

    scored = [
        (score_example(question, example, family), example) for example in examples
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)

    best_score, best_example = scored[0]

    return {
        "best_match": best_example,
        "similarity_score": round(best_score, 2),
    }


def main():
    question = input("Question: ")
    family = input("Family: ")

    result = retrieve(question, family)

    print()
    print(f"Similarity Score: {result['similarity_score']}")
    print()
    print(_example_text(result["best_match"]))


if __name__ == "__main__":
    main()
