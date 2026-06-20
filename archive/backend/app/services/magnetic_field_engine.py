"""Magpylib-backed magnetic field generator engine (Phase 5).

Sits behind ``DiagramRouter`` for ``magnetic_field`` diagrams whose concept is
one of ``solenoid``, ``toroid``, ``circular_loop``, ``straight_wire``, or
``bar_magnet``. Unlike the legacy ``MagneticFieldDiagramGenerator`` (which
hand-rolls pixel positions), this module only emits a JSON-serializable
*render schema* describing the field source categorically - the real
Biot-Savart computation and field-line drawing happens in
``magnetic_field_renderer`` via Magpylib + matplotlib.

    Semantic Schema + Generator Input -> magnetic_field_engine.generate() -> Render Schema
                                       -> magnetic_field_renderer.render() -> SVG
"""

from __future__ import annotations

from typing import Any

_CANVAS = {"width": 800, "height": 400}

# Default viewing convention per source type, used when the semantic schema's
# ``geometry_rules``/``extra`` don't specify one.
_DEFAULT_VIEWING_PLANE: dict[str, str] = {
    "solenoid": "axial",
    "toroid": "axial",
    "circular_loop": "axial",
    "straight_wire": "cross_section",
    "bar_magnet": "side",
}

# Categorical current/field direction -> sign convention used by the renderer
# to flip the Magpylib current/polarization direction.
_CURRENT_SIGN: dict[str, int] = {
    "anticlockwise": 1,
    "out_of_page": 1,
    "clockwise": -1,
    "into_page": -1,
}


def generate(semantic_schema: dict[str, Any], generator_input: dict[str, Any], question_text: str) -> dict[str, Any]:
    """Build a render schema for a Magpylib-backed magnetic field diagram.

    ``question_text`` is accepted for parity with the legacy generators but is
    not used directly - all categorical facts come from the semantic schema's
    ``extra``/``geometry_rules`` (populated by ``PhysicsUnderstandingService``).
    """

    extra = semantic_schema.get("extra") or {}
    geometry_rules = semantic_schema.get("geometry_rules") or {}
    concept = semantic_schema.get("concept") or generator_input.get("concept")
    scenario = semantic_schema.get("scenario") or generator_input.get("scenario")
    required_entities = semantic_schema.get("required_entities") or generator_input.get("entities") or []
    labels_in = semantic_schema.get("labels") or required_entities

    source_type = (
        geometry_rules.get("source_type")
        or extra.get("source_type")
        or extra.get("source")
        or concept
        or "circular_loop"
    )

    current_direction = geometry_rules.get("current_direction") or extra.get("current_direction")
    viewing_plane = (
        geometry_rules.get("viewing_plane") or extra.get("viewing_plane") or _DEFAULT_VIEWING_PLANE.get(source_type, "side")
    )
    current_sign = _CURRENT_SIGN.get(current_direction or "", 1)

    magpylib_model: dict[str, Any] = {
        "source_type": source_type,
        "current_sign": current_sign,
        "viewing_plane": viewing_plane,
    }

    components: list[dict[str, Any]] = []

    if source_type in ("circular_loop", "toroid"):
        components.append({"id": "loop", "type": "current_loop", "label": "Circular Loop"})
        components.append({"id": "field_lines", "type": "field_lines", "label": "Field Lines"})
        if current_direction:
            components.append({"id": "current_direction", "type": "current_direction", "value": current_direction})
    elif source_type == "solenoid":
        turns = int(extra.get("turns") or 8)
        magpylib_model["turns"] = turns
        components.append({"id": "coil", "type": "solenoid", "label": "Solenoid", "turns": turns})
        components.append({"id": "field_lines_inside", "type": "field_lines", "label": "Field Lines Inside"})
        components.append({"id": "field_lines_outside", "type": "field_lines", "label": "Field Lines Outside"})
        if current_direction:
            components.append({"id": "current_direction", "type": "current_direction", "value": current_direction})
    elif source_type == "straight_wire":
        components.append({"id": "wire", "type": "wire", "label": "Straight Wire"})
        components.append({"id": "field_circles", "type": "field_lines", "label": "Field Circles"})
        if current_direction:
            components.append({"id": "current_direction", "type": "current_direction", "value": current_direction})
    else:  # bar_magnet
        pole_orientation = extra.get("pole_orientation", "n_right")
        magpylib_model["pole_orientation"] = pole_orientation
        components.append({"id": "magnet", "type": "bar_magnet", "label": "Bar Magnet", "poles": ["N", "S"]})
        components.append({"id": "field_lines", "type": "field_lines", "label": "Field Lines"})

    labels = [{"text": entity.replace("_", " ").title(), "key": entity} for entity in labels_in]
    if current_direction:
        labels.append({"text": f"Current: {current_direction.replace('_', ' ')}", "key": "current_direction"})

    return {
        "diagram_type": "magnetic_field",
        "title": f"Magnetic Field - {source_type.replace('_', ' ').title()}",
        "canvas": dict(_CANVAS),
        "components": components,
        "connections": [],
        "labels": labels,
        "metadata": {
            "engine": "magpylib",
            "magpylib_model": magpylib_model,
            "source": source_type,
            "entities": required_entities,
            "scenario": scenario,
            "extra": extra,
        },
    }
