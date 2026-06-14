"""Diagram detection and specification generation.

Detection has two layers:

1. **Dataset lookup** - the 214 labeled questions already have a
   human/AI-verified ``requires_diagram`` / ``diagram_type`` label in
   ``diagram_dataset.json``. PYQ questions are matched by ``question_id``
   (or, failing that, by normalized question text).
2. **Heuristic classifier** - for AI-generated or arbitrary questions not
   present in the dataset, a keyword-based classifier infers the diagram
   type from the question wording.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from app.core.exceptions import DataLoadError, InvalidRequestError
from app.models.enums import DiagramType
from app.services.diagram_generators import DIAGRAM_GENERATORS
from app.services.diagram_svg import render_svg

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DiagramDetectionResult:
    """Result of running diagram detection against a question."""

    requires_diagram: bool
    diagram_type: DiagramType
    confidence: float
    reason: str | None = None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


# Pass 1: explicit mentions of a specific diagram type. Checked first because
# they are the strongest signal of the *intended* diagram type.
_EXPLICIT_PATTERNS: list[tuple[DiagramType, list[str]]] = [
    ("ray_diagram", ["ray diagram"]),
    ("circuit", ["circuit diagram"]),
    ("free_body", ["free body diagram", "free-body diagram"]),
    ("magnetic_field", ["magnetic field lines", "field lines"]),
]

# Pass 2: topical keyword sets, checked in priority order when no explicit
# diagram-name phrase is found.
_TOPIC_KEYWORDS: list[tuple[DiagramType, list[str]]] = [
    (
        "circuit",
        [
            "wheatstone bridge",
            "meter bridge",
            "potentiometer",
            "ammeter",
            "voltmeter",
            "galvanometer",
            "given circuit",
            "the circuit",
            "resistors are connected",
            "cells are connected",
            "kirchhoff",
        ],
    ),
    (
        "ray_diagram",
        [
            "convex lens",
            "concave lens",
            "convex mirror",
            "concave mirror",
            "plane mirror",
            "compound microscope",
            "telescope",
            "magnifying power",
            "refraction through",
            "image formed by",
            "prism",
        ],
    ),
    (
        "magnetic_field",
        [
            "magnetic field due to",
            "magnetic field at",
            "solenoid",
            "toroid",
            "current carrying conductor",
            "current-carrying conductor",
            "current loop",
        ],
    ),
    (
        "free_body",
        [
            "free body",
            "forces acting on",
            "block of mass",
            "inclined plane",
            "tension in the string",
            "normal reaction",
        ],
    ),
    (
        "graph",
        [
            "draw the graph",
            "draw a graph",
            "plot a graph",
            "plot the graph",
            "sketch the graph",
            "graph showing the variation",
            "graph between",
        ],
    ),
]


class DiagramService:
    """Provides diagram detection and JSON specification generation."""

    def __init__(self, diagram_dataset_path: Path) -> None:
        self._by_id, self._by_text = self._load(diagram_dataset_path)
        logger.info("DiagramService loaded %d diagram labels from %s", len(self._by_id), diagram_dataset_path)

    @property
    def labeled_count(self) -> int:
        """Number of questions with a known diagram label."""

        return len(self._by_id)

    @staticmethod
    def _load(path: Path) -> tuple[dict[str, dict], dict[str, dict]]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise DataLoadError(f"Diagram dataset file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise DataLoadError(f"Diagram dataset file is not valid JSON: {path}") from exc

        by_id: dict[str, dict] = {}
        by_text: dict[str, dict] = {}
        for entry in raw:
            by_id[entry["question_id"]] = entry
            by_text[_normalize(entry["question"])] = entry
        return by_id, by_text

    def detect(self, question_text: str, question_id: str | None = None) -> DiagramDetectionResult:
        """Detect whether a question requires a diagram and, if so, which type."""

        entry = self._by_id.get(question_id) if question_id else None
        if entry is None:
            entry = self._by_text.get(_normalize(question_text))

        if entry is not None:
            return DiagramDetectionResult(
                requires_diagram=entry.get("requires_diagram", False),
                diagram_type=entry.get("diagram_type", "none"),
                confidence=entry.get("confidence", 0.9),
                reason=entry.get("reason"),
            )

        return self._heuristic_detect(question_text)

    @staticmethod
    def _heuristic_detect(question_text: str) -> DiagramDetectionResult:
        text = _normalize(question_text)

        for diagram_type, phrases in _EXPLICIT_PATTERNS:
            for phrase in phrases:
                if phrase in text:
                    return DiagramDetectionResult(
                        requires_diagram=True,
                        diagram_type=diagram_type,
                        confidence=0.85,
                        reason=f"Question explicitly references '{phrase}'.",
                    )

        for diagram_type, keywords in _TOPIC_KEYWORDS:
            matched = [kw for kw in keywords if kw in text]
            if matched:
                return DiagramDetectionResult(
                    requires_diagram=True,
                    diagram_type=diagram_type,
                    confidence=0.6,
                    reason=f"Question contains keyword(s): {', '.join(matched)}.",
                )

        return DiagramDetectionResult(
            requires_diagram=False,
            diagram_type="none",
            confidence=0.9,
            reason="No diagram-indicating keywords were found in the question.",
        )

    @staticmethod
    def generate_specification(
        diagram_type: DiagramType,
        question_text: str,
        entities: list[str] | None = None,
        scenario: str | None = None,
    ) -> dict:
        """Generate a JSON diagram specification for the given type and question."""

        generator = DIAGRAM_GENERATORS.get(diagram_type)
        if generator is None:
            raise InvalidRequestError(
                f"Cannot generate a specification for diagram_type='{diagram_type}'.",
                detail=f"Supported types: {sorted(DIAGRAM_GENERATORS)}",
            )
        return generator(question_text, entities=entities, scenario=scenario)

    @classmethod
    def build_diagram(
        cls,
        diagram_type: DiagramType,
        question_text: str,
        entities: list[str] | None = None,
        scenario: str | None = None,
    ) -> dict:
        """Generate a full diagram payload: ``{diagram_type, specification, svg}``."""

        specification = cls.generate_specification(diagram_type, question_text, entities=entities, scenario=scenario)
        return {
            "diagram_type": diagram_type,
            "specification": specification,
            "svg": render_svg(specification),
        }
