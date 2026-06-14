"""Physics understanding layer for the Semantic Diagram Intelligence pipeline.

This is the entry point of the new flow:

    Question -> PhysicsAnalyzerService -> Semantic Diagram JSON -> Template Selection
             -> SchemaPopulationService -> Render JSON -> SVG

``PhysicsAnalyzerService`` identifies *what* a diagram is about
(``diagram_type``/``concept``/``scenario``/``entities``) - it NEVER produces
coordinates, positions, sizes, or SVG. The 7-key output shape
(``diagram_required, diagram_type, chapter, concept, scenario, entities,
confidence``) is enforced structurally: ``_from_llm_response`` only reads
those keys, silently discarding any stray geometry an LLM might return.

Cascade mirrors ``ConceptExtractionService``: OpenRouter GPT-4o -> Gemini ->
local taxonomy-driven heuristic (always succeeds).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.models.enums import DiagramType
from app.services.diagram_service import DiagramService
from app.services.diagram_taxonomy_service import DiagramTaxonomyService
from app.services.gemini_service import GeminiService
from app.services.openrouter_service import OpenRouterService
from app.services.prompt_builder import _VALID_DIAGRAM_TYPES

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhysicsAnalysis:
    """The ONLY information an LLM is allowed to produce about a diagram.

    No coordinates, positions, sizes, angles, or SVG - those are computed
    deterministically by ``SchemaPopulationService``.
    """

    diagram_required: bool
    diagram_type: DiagramType
    chapter: str | None
    concept: str | None
    scenario: str | None
    entities: list[str] = field(default_factory=list)
    confidence: float = 0.0


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


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}
    return bool(value)


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


class PhysicsAnalyzerService:
    """Identifies physics concepts/scenarios behind a question - never geometry."""

    def __init__(
        self,
        openrouter_service: OpenRouterService,
        gemini_service: GeminiService,
        diagram_service: DiagramService,
        taxonomy_service: DiagramTaxonomyService,
    ) -> None:
        self._openrouter_service = openrouter_service
        self._gemini_service = gemini_service
        self._diagram_service = diagram_service
        self._taxonomy_service = taxonomy_service

    def analyze(self, question_text: str) -> PhysicsAnalysis:
        """Run the OpenRouter -> Gemini -> local taxonomy fallback cascade."""

        vocabulary = self._taxonomy_service.prompt_vocabulary()

        data = self._openrouter_service.analyze_physics(question_text, vocabulary)
        if data is not None:
            return self._from_llm_response(data)

        data = self._gemini_service.analyze_physics(question_text, vocabulary)
        if data is not None:
            return self._from_llm_response(data)

        return self._local_fallback(question_text)

    @staticmethod
    def _from_llm_response(data: dict) -> PhysicsAnalysis:
        """Coerce an LLM response into a PhysicsAnalysis, reading ONLY the 7 allowed keys.

        Any extra keys (e.g. accidental coordinates/geometry) are silently discarded.
        """

        return PhysicsAnalysis(
            diagram_required=_coerce_bool(data.get("diagram_required")),
            diagram_type=_coerce_diagram_type(data.get("diagram_type")),
            chapter=_coerce_optional_str(data.get("chapter")),
            concept=_coerce_optional_str(data.get("concept")),
            scenario=_coerce_optional_str(data.get("scenario")),
            entities=_coerce_entities(data.get("entities")),
            confidence=_coerce_confidence(data.get("confidence")),
        )

    def _local_fallback(self, question_text: str) -> PhysicsAnalysis:
        detection = self._diagram_service.detect(question_text)
        diagram_type = detection.diagram_type

        text = question_text.lower()
        chapter: str | None = None
        for chapter_name, keywords in _CHAPTER_KEYWORDS:
            if any(keyword in text for keyword in keywords):
                chapter = chapter_name
                break

        concept: str | None = None
        scenario: str | None = None
        entities: list[str] = []
        if diagram_type != "none":
            match = self._taxonomy_service.match_concept(diagram_type, question_text)
            if match is not None:
                concept, scenario = match
                concept_entry = self._taxonomy_service.get_concept_entry(diagram_type, concept)
                if concept_entry:
                    entities = list(concept_entry.get("entities", []))

        return PhysicsAnalysis(
            diagram_required=detection.requires_diagram,
            diagram_type=diagram_type,
            chapter=chapter,
            concept=concept,
            scenario=scenario,
            entities=entities,
            confidence=detection.confidence,
        )
