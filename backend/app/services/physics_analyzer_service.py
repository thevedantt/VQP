"""Physics understanding layer for the Dynamic Physics Semantic Schema pipeline.

This is the entry point of the flow:

    Question -> PhysicsAnalyzerService -> Dynamic Semantic Schema -> Template Selection
             -> SchemaPopulationService -> Render JSON -> SVG

``PhysicsAnalyzerService`` acts as a *Physics Semantic Analyst*: it
understands the question, explains what is being asked, identifies the
underlying concept, and emits a dynamic, concept-specific semantic schema
(``PhysicsAnalysis``). It NEVER produces coordinates, positions, sizes, or
SVG - ``_from_llm_response`` only reads the keys of the mandated schema,
silently discarding any stray geometry an LLM might return.

Cascade mirrors ``ConceptExtractionService``: OpenRouter GPT-4o -> Gemini ->
local taxonomy-driven heuristic (always succeeds).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.models.enums import DiagramType
from app.services.diagram_service import DiagramService
from app.services.diagram_taxonomy_service import DiagramTaxonomyService
from app.services.diagram_template_service import DiagramTemplateService
from app.services.gemini_service import GeminiService
from app.services.openrouter_service import OpenRouterService
from app.services.prompt_builder import _VALID_DIAGRAM_TYPES

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UnderstandingLayer:
    """The "did the model understand the question" inspection layer."""

    what_is_the_question_asking: str = ""
    what_physics_concept_is_involved: str = ""
    why_is_a_diagram_required: str = ""
    what_must_be_visible: list[str] = field(default_factory=list)
    what_labels_must_be_present: list[str] = field(default_factory=list)
    what_examiner_expects_to_see: str = ""


@dataclass(frozen=True)
class PhysicsAnalysis:
    """The dynamic, concept-specific semantic schema for a diagram.

    No coordinates, positions, sizes, angles, or SVG - those are computed
    deterministically by ``SchemaPopulationService``/``diagram_generators``.
    ``extra`` is intentionally free-form and concept-specific (e.g. lens
    type + ray rules for a ray diagram, diode count for a rectifier).
    """

    diagram_required: bool
    diagram_type: DiagramType
    chapter: str | None
    concept: str | None
    scenario: str | None
    confidence: float = 0.0
    candidate_concepts: list[str] = field(default_factory=list)
    required_entities: list[str] = field(default_factory=list)
    relationships: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    visual_rules: list[str] = field(default_factory=list)
    validation: list[str] = field(default_factory=list)
    understanding: UnderstandingLayer = field(default_factory=UnderstandingLayer)
    extra: dict[str, Any] = field(default_factory=dict)


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

# Concept name -> categorical lens/mirror type, used by the local fallback to
# populate a concept-specific ``extra`` block from the diagram taxonomy.
_LENS_TYPES: dict[str, str] = {"convex_lens": "convex", "concave_lens": "concave"}
_MIRROR_TYPES: dict[str, str] = {"concave_mirror": "concave", "convex_mirror": "convex", "plane_mirror": "plane"}


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}
    return bool(value)


def _coerce_str_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _coerce_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


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


def _coerce_str(value: object) -> str:
    return _coerce_optional_str(value) or ""


def _coerce_understanding(value: object) -> UnderstandingLayer:
    data = value if isinstance(value, dict) else {}
    return UnderstandingLayer(
        what_is_the_question_asking=_coerce_str(data.get("what_is_the_question_asking")),
        what_physics_concept_is_involved=_coerce_str(data.get("what_physics_concept_is_involved")),
        why_is_a_diagram_required=_coerce_str(data.get("why_is_a_diagram_required")),
        what_must_be_visible=_coerce_str_list(data.get("what_must_be_visible")),
        what_labels_must_be_present=_coerce_str_list(data.get("what_labels_must_be_present")),
        what_examiner_expects_to_see=_coerce_str(data.get("what_examiner_expects_to_see")),
    )


class PhysicsAnalyzerService:
    """Acts as a Physics Semantic Analyst - identifies concepts/scenarios and
    emits a dynamic, concept-specific semantic schema. Never produces geometry."""

    def __init__(
        self,
        openrouter_service: OpenRouterService,
        gemini_service: GeminiService,
        diagram_service: DiagramService,
        taxonomy_service: DiagramTaxonomyService,
        diagram_template_service: DiagramTemplateService,
    ) -> None:
        self._openrouter_service = openrouter_service
        self._gemini_service = gemini_service
        self._diagram_service = diagram_service
        self._taxonomy_service = taxonomy_service
        self._diagram_template_service = diagram_template_service

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
        """Coerce an LLM response into a PhysicsAnalysis, reading ONLY the
        keys of the mandated dynamic schema.

        Any extra keys (e.g. accidental coordinates/geometry) are silently
        discarded.
        """

        return PhysicsAnalysis(
            diagram_required=_coerce_bool(data.get("diagram_required")),
            diagram_type=_coerce_diagram_type(data.get("diagram_type")),
            chapter=_coerce_optional_str(data.get("chapter")),
            concept=_coerce_optional_str(data.get("concept")),
            scenario=_coerce_optional_str(data.get("scenario")),
            confidence=_coerce_confidence(data.get("confidence")),
            candidate_concepts=_coerce_str_list(data.get("candidate_concepts")),
            required_entities=_coerce_str_list(data.get("required_entities")),
            relationships=_coerce_str_list(data.get("relationships")),
            constraints=_coerce_str_list(data.get("constraints")),
            visual_rules=_coerce_str_list(data.get("visual_rules")),
            validation=_coerce_str_list(data.get("validation")),
            understanding=_coerce_understanding(data.get("understanding")),
            extra=_coerce_dict(data.get("extra")),
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
        required_entities: list[str] = []
        if diagram_type != "none":
            match = self._taxonomy_service.match_concept(diagram_type, question_text)
            if match is not None:
                concept, scenario = match
                concept_entry = self._taxonomy_service.get_concept_entry(diagram_type, concept)
                if concept_entry:
                    required_entities = list(concept_entry.get("entities", []))

        candidate_concepts = [concept] if concept else []
        visual_rules = [f"Show {entity.replace('_', ' ')}." for entity in required_entities]
        validation = (
            [f"Diagram must include: {', '.join(entity.replace('_', ' ') for entity in required_entities)}."]
            if required_entities
            else []
        )

        _, template = self._diagram_template_service.select(diagram_type, concept, scenario)
        extra = self._fallback_extra(diagram_type, concept, scenario, template)
        understanding = self._fallback_understanding(diagram_type, concept, scenario, required_entities, detection.reason)

        return PhysicsAnalysis(
            diagram_required=detection.requires_diagram,
            diagram_type=diagram_type,
            chapter=chapter,
            concept=concept,
            scenario=scenario,
            confidence=detection.confidence,
            candidate_concepts=candidate_concepts,
            required_entities=required_entities,
            relationships=[],
            constraints=[],
            visual_rules=visual_rules,
            validation=validation,
            understanding=understanding,
            extra=extra,
        )

    @staticmethod
    def _fallback_understanding(
        diagram_type: DiagramType,
        concept: str | None,
        scenario: str | None,
        required_entities: list[str],
        reason: str | None,
    ) -> UnderstandingLayer:
        if diagram_type == "none":
            return UnderstandingLayer(
                what_is_the_question_asking="This question does not appear to require a diagram to answer.",
                what_physics_concept_is_involved="Not identified by the local fallback.",
                why_is_a_diagram_required=reason or "No diagram-indicating keywords were found in the question.",
                what_must_be_visible=[],
                what_labels_must_be_present=[],
                what_examiner_expects_to_see="A written explanation and/or numerical answer, without a diagram.",
            )

        concept_label = (concept or diagram_type).replace("_", " ")
        diagram_label = diagram_type.replace("_", " ")
        scenario_label = (scenario or "default").replace("_", " ")

        return UnderstandingLayer(
            what_is_the_question_asking=f"The question asks the student to analyze and draw a {diagram_label} for {concept_label}.",
            what_physics_concept_is_involved=concept_label,
            why_is_a_diagram_required=reason or f"A {diagram_label} is the standard way to represent {concept_label}.",
            what_must_be_visible=required_entities,
            what_labels_must_be_present=required_entities,
            what_examiner_expects_to_see=f"A correctly labeled {diagram_label} for the {scenario_label} scenario of {concept_label}.",
        )

    @staticmethod
    def _fallback_extra(
        diagram_type: DiagramType,
        concept: str | None,
        scenario: str | None,
        template: dict,
    ) -> dict[str, Any]:
        """Build a concept-specific ``extra`` block from the matched template's
        ``scenario_rules`` (reuses existing categorical template data instead
        of inventing new heuristics)."""

        scenario_rules = template.get("scenario_rules", {})
        rules = scenario_rules.get(scenario) or scenario_rules.get(template.get("default_scenario")) or {}

        if diagram_type == "ray_diagram":
            extra: dict[str, Any] = {}
            if concept in _LENS_TYPES:
                extra["lens_type"] = _LENS_TYPES[concept]
                ray_rules = ["parallel_ray", "optical_center_ray"]
            elif concept in _MIRROR_TYPES:
                extra["mirror_type"] = _MIRROR_TYPES[concept]
                ray_rules = ["parallel_ray", "pole_ray"]
            else:
                ray_rules = ["parallel_ray", "optical_center_ray"]

            if scenario:
                extra["object_position"] = scenario

            nature, orientation, size = rules.get("image_nature"), rules.get("orientation"), rules.get("size")
            if nature and orientation and size:
                extra["expected_image"] = f"{nature}_{orientation}_{size}"

            extra["ray_rules"] = ray_rules
            return extra

        if diagram_type == "circuit":
            if concept == "full_wave_rectifier":
                return {
                    "rectifier_type": scenario or "center_tapped",
                    "number_of_diodes": 2,
                    "requires_transformer": True,
                    "requires_load_resistor": True,
                    "ac_source": True,
                    "dc_output": True,
                }
            if concept == "wheatstone_bridge":
                return {"bridge_type": "wheatstone", "number_of_resistors": 4}
            return {}

        if diagram_type == "free_body":
            return {
                "surface": "inclined" if rules.get("on_incline") else "horizontal",
                "object": "block",
                "forces": list(rules.get("forces", [])),
            }

        if diagram_type == "graph":
            extra = {"graph_type": concept or "generic"}
            if rules.get("x_label"):
                extra["x_axis"] = rules["x_label"]
            if rules.get("y_label"):
                extra["y_axis"] = rules["y_label"]
            if rules.get("curve_type"):
                extra["curve_shape"] = rules["curve_type"]
            return extra

        if diagram_type == "magnetic_field":
            source = rules.get("source") or concept or scenario
            return {"source": source} if source else {}

        return {}
