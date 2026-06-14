"""Concept and diagram-entity extraction for AI-generated diagram questions.

PART 1/2 of the OpenRouter upgrade: given a question's text, identify its
chapter, concept, diagram type, scenario and required diagram entities -
the model never draws, it only identifies structured metadata that the
physics-specific diagram generators (``diagram_generators.py``) consume.

Cascade: OpenRouter GPT-4o -> Gemini -> local heuristic (dataset/keyword
based, via ``DiagramService``). Only invoked for AI-generated questions that
require a diagram and whose generation response did not already include
``diagram`` entities/scenario (i.e. the Gemini/local generation tiers).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from app.models.enums import DiagramType
from app.services.diagram_service import DiagramService
from app.services.gemini_service import GeminiService
from app.services.openrouter_service import OpenRouterService
from app.services.prompt_builder import _VALID_DIAGRAM_TYPES

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConceptExtractionResult:
    """Structured concept/diagram metadata extracted from a question's text."""

    chapter: str | None
    concept: str | None
    diagram_type: DiagramType
    scenario: str | None
    entities: list[str] = field(default_factory=list)
    confidence: float = 0.0


# Default diagram entities per type, used when the local heuristic fallback
# cannot derive a more specific entity list.
_DEFAULT_ENTITIES: dict[str, list[str]] = {
    "circuit": ["battery", "resistor", "connecting_wires"],
    "ray_diagram": ["principal_axis", "object", "image", "optical_element"],
    "free_body": ["block", "weight", "normal_force"],
    "magnetic_field": ["field_source", "field_lines"],
    "graph": ["x_axis", "y_axis", "curve"],
}

# Topic keywords used to infer the NCERT chapter for the local fallback.
_CHAPTER_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Electric Charges and Fields", ["electric charge", "coulomb", "electric field", "gauss"]),
    ("Electrostatic Potential and Capacitance", ["potential", "capacitor", "capacitance", "dielectric"]),
    ("Current Electricity", ["current", "resistance", "resistor", "ohm", "wheatstone", "potentiometer", "emf", "cell"]),
    ("Moving Charges and Magnetism", ["magnetic field", "ampere", "biot-savart", "solenoid", "cyclotron", "lorentz"]),
    ("Magnetism and Matter", ["bar magnet", "magnetism", "magnetic dipole", "earth's magnetic field"]),
    ("Electromagnetic Induction", ["induced emf", "faraday", "lenz", "electromagnetic induction", "eddy current"]),
    ("Alternating Current", ["alternating current", "ac circuit", "rms", "impedance", "reactance", "transformer", "rectifier"]),
    ("Electromagnetic Waves", ["electromagnetic wave", "electromagnetic spectrum", "displacement current"]),
    ("Ray Optics", ["lens", "mirror", "refraction", "reflection", "ray diagram", "telescope", "microscope"]),
    ("Wave Optics", ["interference", "diffraction", "polarization", "wavefront", "young's experiment"]),
    ("Dual Nature of Radiation and Matter", ["photoelectric", "photon", "de broglie", "work function"]),
    ("Atoms", ["bohr", "atomic model", "hydrogen spectrum", "energy levels"]),
    ("Nuclei", ["nucleus", "radioactivity", "binding energy", "half-life", "fission", "fusion"]),
    ("Semiconductor Electronics", ["diode", "transistor", "semiconductor", "p-n junction", "logic gate"]),
]


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _coerce_entities(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(e) for e in value if str(e).strip()]
    return []


def _coerce_diagram_type(value: object) -> DiagramType:
    if isinstance(value, str) and value in _VALID_DIAGRAM_TYPES:
        return value  # type: ignore[return-value]
    return "none"


def _coerce_confidence(value: object) -> float:
    try:
        confidence = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, confidence))


def _coerce_optional_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


class ConceptExtractionService:
    """Extracts concept/diagram metadata for AI-generated diagram questions."""

    def __init__(
        self,
        openrouter_service: OpenRouterService,
        gemini_service: GeminiService,
        diagram_service: DiagramService,
    ) -> None:
        self._openrouter_service = openrouter_service
        self._gemini_service = gemini_service
        self._diagram_service = diagram_service

    def extract(self, question_text: str) -> ConceptExtractionResult:
        """Extract concept/diagram metadata, cascading across providers."""

        data = self._openrouter_service.extract_concept(question_text)
        if data is not None:
            return self._from_llm_response(data)

        data = self._gemini_service.extract_concept(question_text)
        if data is not None:
            return self._from_llm_response(data)

        return self._local_fallback(question_text)

    @staticmethod
    def _from_llm_response(data: dict) -> ConceptExtractionResult:
        return ConceptExtractionResult(
            chapter=_coerce_optional_str(data.get("chapter")),
            concept=_coerce_optional_str(data.get("concept")),
            diagram_type=_coerce_diagram_type(data.get("diagram_type")),
            scenario=_coerce_optional_str(data.get("scenario")),
            entities=_coerce_entities(data.get("entities")),
            confidence=_coerce_confidence(data.get("confidence")),
        )

    def _local_fallback(self, question_text: str) -> ConceptExtractionResult:
        detection = self._diagram_service.detect(question_text)
        diagram_type = detection.diagram_type

        text = question_text.lower()
        chapter: str | None = None
        for chapter_name, keywords in _CHAPTER_KEYWORDS:
            if any(keyword in text for keyword in keywords):
                chapter = chapter_name
                break

        entities = list(_DEFAULT_ENTITIES.get(diagram_type, []))
        concept = _slugify(diagram_type) if diagram_type != "none" else None

        return ConceptExtractionResult(
            chapter=chapter,
            concept=concept,
            diagram_type=diagram_type,
            scenario=None,
            entities=entities,
            confidence=detection.confidence,
        )
