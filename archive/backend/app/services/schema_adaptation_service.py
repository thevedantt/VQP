"""Schema Adaptation Service (V1).

Takes a new question and a retrieved library schema, then produces an
"Updated Schema" suitable for the diagram generators.

Preserves:
  - renderer_type
  - diagram_family
  - geometry_rules
  - generation_rules

Updates:
  - scenario
  - variable_parameters
  - labels
  - description
"""

from __future__ import annotations

from typing import Any

from app.services.diagram_retrieval_service import (
    _LENS_TYPES,
    _MAGNETIC_DEFAULT_DIRECTION,
    _MAGNETIC_VIEWING_PLANE,
    _MIRROR_TYPES,
    _detect_current_direction,
)


class SchemaAdaptationService:
    """Adapts a retrieved library schema to a new question."""

    @staticmethod
    def adapt(
        question_text: str,
        retrieved_schema: dict[str, Any],
        classification: dict[str, str],
    ) -> dict[str, Any]:
        """Return an updated schema dict preserving key structure and updating
        scenario-specific fields.

        The returned dict is designed to be consumed by the existing
        diagram generators (``diagram_generators.py``) via ``rules``
        and ``extra`` parameters.
        """
        classification_renderer = classification.get("renderer_type", "")
        classification_concept = classification.get("concept", "")
        classification_scenario = classification.get("scenario", "")

        # Preserved fields.
        adapted: dict[str, Any] = {
            "renderer_type": classification_renderer,
            "diagram_family": retrieved_schema.get("diagram_family", ""),
            "geometry_rules": dict(retrieved_schema.get("geometry_rules", {})),
            "generation_rules": list(retrieved_schema.get("generation_rules", [])),
        }

        # Updated fields.
        adapted["concept"] = classification_concept or retrieved_schema.get("concept", "")
        adapted["scenario"] = classification_scenario or retrieved_schema.get("scenario", "default")
        adapted["variable_parameters"] = list(retrieved_schema.get("variable_parameters", []))
        adapted["labels"] = list(retrieved_schema.get("required_labels", []))
        adapted["description"] = retrieved_schema.get("diagram_description", "")
        adapted["required_entities"] = list(retrieved_schema.get("required_entities", []))
        adapted["relationships"] = list(retrieved_schema.get("relationships", []))
        adapted["extra"] = dict(retrieved_schema.get("extra", {}))

        # Build generator-compatible rules and extra blocks.
        adapted["rules"] = SchemaAdaptationService._build_rules(
            classification_renderer, classification_concept, classification_scenario,
            retrieved_schema,
        )
        adapted["extra"] = SchemaAdaptationService._build_extra(
            classification_renderer, classification_concept, classification_scenario,
            retrieved_schema, question_text,
        )

        return adapted

    @staticmethod
    def _build_rules(
        renderer_type: str,
        concept: str,
        scenario: str,
        retrieved_schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a ``rules`` dict that the diagram generators accept.

        Maps library schema fields (geometry_rules, generation_rules)
        into the categorical ``rules`` shape expected by each generator.
        """
        rules: dict[str, Any] = {}
        geometry = retrieved_schema.get("geometry_rules", {})

        if renderer_type == "free_body":
            if geometry.get("incline") or geometry.get("on_incline"):
                rules["on_incline"] = True
            forces = []
            if geometry.get("tension_present"):
                forces.append("tension")
            if geometry.get("friction_present"):
                forces.append("friction")
            if geometry.get("applied_force_present"):
                forces.append("applied_force")
            if forces:
                rules["forces"] = forces

        elif renderer_type == "circuit":
            layout = retrieved_schema.get("diagram_family", "").lower()
            if "wheatstone" in layout or "bridge" in layout:
                rules["layout"] = "wheatstone_bridge"
            elif "rectifier" in layout:
                rules["layout"] = "full_wave_rectifier_center_tapped"
            else:
                rules["layout"] = "series_parallel"

        elif renderer_type == "graph":
            rules["curve_type"] = geometry.get("curve_type", "linear")

        elif renderer_type == "ray_optics":
            if concept in _LENS_TYPES:
                rules["lens_type"] = _LENS_TYPES[concept]
            elif concept in _MIRROR_TYPES:
                rules["mirror_type"] = _MIRROR_TYPES[concept]
            rules["object_position"] = geometry.get("object_position", "between_f_and_2f")
            rules["image_nature"] = geometry.get("image_nature", "real")
            rules["orientation"] = geometry.get("orientation", "inverted")
            rules["size"] = geometry.get("size", "same")

        elif renderer_type == "magnetic_field":
            source = retrieved_schema.get("concept", scenario)
            if source:
                rules["source"] = source

        return rules

    @staticmethod
    def _build_extra(
        renderer_type: str,
        concept: str,
        scenario: str,
        retrieved_schema: dict[str, Any],
        question_text: str,
    ) -> dict[str, Any]:
        """Build an ``extra`` dict that the diagram generators accept.

        Provides concept-specific hints from the retrieved schema.
        """
        extra: dict[str, Any] = {}
        geometry = retrieved_schema.get("geometry_rules", {})
        retrieved_extra = retrieved_schema.get("extra", {})
        generation_rules = retrieved_schema.get("generation_rules", [])

        if renderer_type == "free_body":
            extra["surface"] = "inclined" if geometry.get("on_incline") else "horizontal"
            extra["object"] = "block"
            extra["forces"] = []

        elif renderer_type == "circuit":
            diagram_family = retrieved_schema.get("diagram_family", "").lower()
            if "rectifier" in diagram_family:
                extra["rectifier_type"] = scenario or "center_tapped"
                extra["number_of_diodes"] = 2
                extra["requires_transformer"] = True
                extra["requires_load_resistor"] = True
            elif "bridge" in diagram_family:
                extra["bridge_type"] = "wheatstone"
                extra["number_of_resistors"] = 4
            else:
                extra["network_type"] = retrieved_extra.get("network_type", "series")

        elif renderer_type == "graph":
            extra["graph_type"] = concept or "generic"
            if "curve_type" in retrieved_extra:
                extra["curve_shape"] = retrieved_extra["curve_type"]
            elif generation_rules:
                extra["curve_shape"] = "linear"

        elif renderer_type == "ray_optics":
            if concept in _LENS_TYPES:
                extra["lens_type"] = _LENS_TYPES[concept]
            elif concept in _MIRROR_TYPES:
                extra["mirror_type"] = _MIRROR_TYPES[concept]
            extra["ray_rules"] = ["parallel_ray", "optical_center_ray"]

        elif renderer_type == "magnetic_field":
            source = concept or scenario
            if source:
                extra["source_type"] = source
                direction = _detect_current_direction(question_text) or _MAGNETIC_DEFAULT_DIRECTION.get(source)
                if direction:
                    extra["current_direction"] = direction
                extra["viewing_plane"] = _MAGNETIC_VIEWING_PLANE.get(source, "side")

        # Carry over any equations or special flags from retrieved schema.
        if "equations_visible" in retrieved_extra:
            extra["equations_visible"] = list(retrieved_extra["equations_visible"])

        return extra
