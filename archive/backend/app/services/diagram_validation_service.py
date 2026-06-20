"""Diagram validation layer (Phase 6).

The last stage of the pipeline: checks whether the rendered diagram actually
satisfies what the semantic schema said it must contain (required entities,
labels, NCERT-expected labels, examiner expectations, constraints), and
produces a score + report for the playground.

    Semantic Schema + Render Schema + SVG -> DiagramValidationService -> Validation Report
"""

from __future__ import annotations

import re
from typing import Any

# Composite score weighting: required entities/labels dominate, NCERT
# alignment and examiner-expectation overlap are secondary signals.
_ENTITY_WEIGHT = 50.0
_LABEL_WEIGHT = 30.0
_NCERT_WEIGHT = 10.0
_EXAMINER_WEIGHT = 10.0


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _haystack(render_schema: dict[str, Any], svg: str) -> str:
    """Flatten the render schema's textual content + SVG into a single
    lowercase, normalized string to search for entity/label mentions."""

    parts: list[str] = [svg]

    for component in render_schema.get("components", []):
        if isinstance(component, dict):
            for value in component.values():
                if isinstance(value, str):
                    parts.append(value)
                elif isinstance(value, list):
                    parts.extend(str(v) for v in value)

    for label in render_schema.get("labels", []):
        if isinstance(label, dict):
            for value in label.values():
                if isinstance(value, str):
                    parts.append(value)
        else:
            parts.append(str(label))

    metadata = render_schema.get("metadata", {})
    if isinstance(metadata, dict):
        for value in metadata.values():
            if isinstance(value, (str, int, float)):
                parts.append(str(value))
            elif isinstance(value, list):
                parts.extend(str(v) for v in value)

    return _normalize(" ".join(parts))


def _present(item: str, haystack: str) -> bool:
    normalized = _normalize(item)
    if not normalized:
        return True
    if normalized in haystack:
        return True
    # Fall back to "all significant words present" so e.g. "field lines
    # inside" matches a haystack containing "field_lines_inside".
    words = [w for w in normalized.split(" ") if len(w) > 2]
    return bool(words) and all(word in haystack for word in words)


class DiagramValidationService:
    """Checks a render schema/SVG against the semantic schema's expectations."""

    def validate(self, semantic_schema: dict[str, Any], render_schema: dict[str, Any], svg: str) -> dict[str, Any]:
        haystack = _haystack(render_schema, svg)

        required_entities: list[str] = semantic_schema.get("required_entities") or []
        labels: list[str] = semantic_schema.get("labels") or []
        textbook_context = semantic_schema.get("textbook_context") or {}
        expected_labels: list[str] = textbook_context.get("expected_labels") or []
        understanding = semantic_schema.get("understanding") or {}
        constraints: list[str] = semantic_schema.get("constraints") or []

        missing_entities = [e for e in required_entities if not _present(e, haystack)]
        missing_labels = [lbl for lbl in labels if not _present(lbl, haystack)]
        missing_ncert_labels = [lbl for lbl in expected_labels if not _present(lbl, haystack)]

        warnings: list[str] = []
        if missing_ncert_labels:
            warnings.append(
                "NCERT-expected labels not found in diagram: " + ", ".join(missing_ncert_labels)
            )

        examiner_expectation = understanding.get("what_examiner_expects_to_see") or ""
        examiner_overlap_score = 1.0
        if examiner_expectation:
            expectation_words = [w for w in _normalize(examiner_expectation).split(" ") if len(w) > 3]
            if expectation_words:
                matched = sum(1 for word in expectation_words if word in haystack)
                examiner_overlap_score = matched / len(expectation_words)
                if examiner_overlap_score < 0.3:
                    warnings.append("Diagram may not meet the examiner's expectations: " + examiner_expectation)

        for constraint in constraints:
            words = [w for w in _normalize(constraint).split(" ") if len(w) > 3]
            if words and not any(word in haystack for word in words):
                warnings.append(f"Constraint may not be satisfied: {constraint}")

        if not svg:
            warnings.append("No diagram was rendered.")

        entity_score = (
            1.0 - (len(missing_entities) / len(required_entities)) if required_entities else 1.0
        )
        label_score = 1.0 - (len(missing_labels) / len(labels)) if labels else 1.0
        ncert_score = 1.0 - (len(missing_ncert_labels) / len(expected_labels)) if expected_labels else 1.0

        diagram_score = (
            entity_score * _ENTITY_WEIGHT
            + label_score * _LABEL_WEIGHT
            + ncert_score * _NCERT_WEIGHT
            + examiner_overlap_score * _EXAMINER_WEIGHT
        )
        if not svg:
            diagram_score = 0.0

        return {
            "diagram_score": round(diagram_score, 1),
            "missing_entities": missing_entities,
            "missing_labels": missing_labels,
            "warnings": warnings,
        }
