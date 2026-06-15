"""Diagram specification generators.

Each generator inspects the question text for domain keywords and returns a
structured, renderable specification:

    {
        "diagram_type": "...",
        "title": "...",
        "canvas": {"width": 800, "height": 400},
        "components": [...],
        "connections": [...],
        "labels": [...],
        "metadata": {...},
    }

``components``/``connections``/``labels`` use plain coordinates on the
``canvas`` so the SVG generation layer (``diagram_svg.py``) can render them
directly without any further interpretation.
"""

from __future__ import annotations

import math
import re
from typing import Any

_CANVAS = {"width": 800, "height": 400}


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _endpoint(cx: float, cy: float, angle_deg: float, length: float) -> dict[str, float]:
    """Return ``{"x2": ..., "y2": ...}`` at ``length`` from (cx, cy) at ``angle_deg``.

    Angle convention: 0deg points right, 90deg points up (visually), matching
    everyday usage even though SVG's y-axis grows downward.
    """

    rad = math.radians(angle_deg)
    return {
        "x2": round(cx + length * math.cos(rad), 1),
        "y2": round(cy - length * math.sin(rad), 1),
    }


class FreeBodyDiagramGenerator:
    """Builds a free body diagram: an object with labeled force vectors."""

    @classmethod
    def generate(
        cls,
        question_text: str,
        entities: list[str] | None = None,
        scenario: str | None = None,
        rules: dict[str, Any] | None = None,
        concept: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = question_text.lower()
        extra = extra or {}

        on_incline = _contains_any(text, ["incline", "inclined plane", "slope", "ramp"])
        has_friction = _contains_any(text, ["friction"])
        has_tension = _contains_any(text, ["tension", "string", "rope", "wire is attached", "pulley"])
        has_applied_force = _contains_any(text, ["applied force", "force f", "pushed", "pulled", "push", "pull"])

        if rules:
            if "on_incline" in rules:
                on_incline = bool(rules["on_incline"])
            forces = set(rules.get("forces", []))
            if forces:
                has_friction = "friction" in forces
                has_tension = "tension" in forces
                has_applied_force = "applied_force" in forces
        elif extra:
            if "surface" in extra:
                on_incline = extra.get("surface") == "inclined"
            forces = set(extra.get("forces", []))
            if forces:
                has_friction = "friction" in forces
                has_tension = "tension" in forces
                has_applied_force = "applied_force" in forces

        components: list[dict[str, Any]] = []
        labels: list[dict[str, Any]] = []

        if on_incline:
            angle = 30.0
            base_left = (120.0, 360.0)
            base_right = (560.0, 360.0)
            incline_height = (base_right[0] - base_left[0]) * math.tan(math.radians(angle))
            apex = (base_right[0], base_right[1] - incline_height)

            components.append(
                {
                    "id": "incline",
                    "type": "incline",
                    "points": [list(base_left), list(base_right), list(apex)],
                }
            )
            labels.append({"text": f"{angle:.0f} deg", "x": base_right[0] - 50, "y": base_right[1] - 14, "anchor": "middle"})

            t = 0.45
            cx = base_left[0] + (apex[0] - base_left[0]) * t
            cy = base_left[1] + (apex[1] - base_left[1]) * t
            box_w, box_h = 90.0, 50.0
            components.append(
                {
                    "id": "object",
                    "type": "box",
                    "x": cx - box_w / 2,
                    "y": cy - box_h / 2,
                    "width": box_w,
                    "height": box_h,
                    "rotation": -angle,
                    "label": "Block",
                }
            )

            components.append({"id": "weight", "type": "arrow", "x1": cx, "y1": cy, **_endpoint(cx, cy, -90, 100), "label": "mg"})
            components.append({"id": "normal", "type": "arrow", "x1": cx, "y1": cy, **_endpoint(cx, cy, 90 - angle, 90), "label": "N"})
            if has_friction:
                components.append({"id": "friction", "type": "arrow", "x1": cx, "y1": cy, **_endpoint(cx, cy, angle, 70), "label": "f"})
            if has_tension:
                components.append({"id": "tension", "type": "arrow", "x1": cx, "y1": cy, **_endpoint(cx, cy, angle, 130), "label": "T"})
            if has_applied_force:
                components.append({"id": "applied_force", "type": "arrow", "x1": cx, "y1": cy, **_endpoint(cx, cy, 0, 90), "label": "F"})
        else:
            ground_y = 320.0
            components.append({"id": "ground", "type": "ground", "x1": 100, "y1": ground_y, "x2": 700, "y2": ground_y})

            box_w, box_h = 110.0, 60.0
            cx, cy = 400.0, ground_y - box_h / 2
            components.append(
                {
                    "id": "object",
                    "type": "box",
                    "x": cx - box_w / 2,
                    "y": cy - box_h / 2,
                    "width": box_w,
                    "height": box_h,
                    "rotation": 0,
                    "label": "Block",
                }
            )

            components.append({"id": "weight", "type": "arrow", "x1": cx, "y1": cy, **_endpoint(cx, cy, -90, 100), "label": "mg"})
            components.append({"id": "normal", "type": "arrow", "x1": cx, "y1": cy, **_endpoint(cx, cy, 90, 100), "label": "N"})
            if has_friction:
                components.append({"id": "friction", "type": "arrow", "x1": cx, "y1": cy, **_endpoint(cx, cy, 180, 90), "label": "f"})
            if has_tension:
                components.append({"id": "tension", "type": "arrow", "x1": cx, "y1": cy, **_endpoint(cx, cy, 45, 110), "label": "T"})
            if has_applied_force:
                components.append({"id": "applied_force", "type": "arrow", "x1": cx, "y1": cy, **_endpoint(cx, cy, 0, 110), "label": "F"})

        return {
            "diagram_type": "free_body",
            "title": "Free Body Diagram",
            "canvas": dict(_CANVAS),
            "components": components,
            "connections": [],
            "labels": labels,
            "metadata": {
                "on_incline": on_incline,
                "has_friction": has_friction,
                "has_tension": has_tension,
                "has_applied_force": has_applied_force,
                "entities": entities or [],
                "scenario": scenario,
                "extra": extra,
            },
        }


_CIRCUIT_COMPONENT_KEYWORDS: list[tuple[str, list[str]]] = [
    ("battery", ["battery", "cell", "emf", "e.m.f"]),
    ("resistor", ["resistor", "resistance"]),
    ("ammeter", ["ammeter"]),
    ("voltmeter", ["voltmeter"]),
    ("galvanometer", ["galvanometer"]),
    ("capacitor", ["capacitor"]),
    ("switch", ["switch", "key k"]),
    ("rheostat", ["rheostat", "potentiometer"]),
]

# Maps concept-extraction diagram entity names (snake_case or freeform) to
# circuit component types renderable by the schemdraw/custom SVG renderers.
_ENTITY_COMPONENT_MAP: dict[str, str] = {
    "battery": "battery",
    "cell": "battery",
    "transformer": "transformer",
    "diode": "diode",
    "rectifier": "diode",
    "resistor": "resistor",
    "load_resistor": "resistor",
    "load": "resistor",
    "capacitor": "capacitor",
    "inductor": "inductor",
    "switch": "switch",
    "ammeter": "ammeter",
    "voltmeter": "voltmeter",
    "galvanometer": "galvanometer",
    "rheostat": "rheostat",
    "potentiometer": "rheostat",
}


class CircuitDiagramGenerator:
    """Builds a circuit diagram: a wire loop with electrical components."""

    @classmethod
    def generate(
        cls,
        question_text: str,
        entities: list[str] | None = None,
        scenario: str | None = None,
        rules: dict[str, Any] | None = None,
        concept: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = question_text.lower()
        extra = extra or {}
        layout = (rules or {}).get("layout")

        if layout == "full_wave_rectifier_center_tapped" or (not rules and extra.get("rectifier_type")):
            return cls._generate_full_wave_rectifier(entities, scenario, extra)

        component_types: list[tuple[str, str]] = []
        for component_type, keywords in _CIRCUIT_COMPONENT_KEYWORDS:
            if _contains_any(text, keywords):
                component_types.append((component_type, component_type))

        for entity in entities or []:
            mapped_type = _ENTITY_COMPONENT_MAP.get(_slugify(entity))
            if mapped_type and not any(t == mapped_type for _, t in component_types):
                component_types.append((mapped_type, mapped_type))

        resistor_labels = sorted(set(re.findall(r"\bR[\d]\b", question_text)))
        if resistor_labels:
            component_types = [c for c in component_types if c[1] != "resistor"]
            for resistor_label in resistor_labels:
                component_types.append((resistor_label, "resistor"))

        if not component_types:
            component_types = [("battery", "battery"), ("R1", "resistor")]

        is_bridge = (
            layout == "wheatstone_bridge"
            or extra.get("bridge_type") == "wheatstone"
            or _contains_any(text, ["wheatstone bridge", "meter bridge"])
        )

        components: list[dict[str, Any]] = []
        connections: list[dict[str, Any]] = []

        if is_bridge:
            top, right, bottom, left = (400.0, 70.0), (650.0, 200.0), (400.0, 330.0), (150.0, 200.0)
            components.append({"id": "loop", "type": "wire_loop", "points": [list(top), list(right), list(bottom), list(left)]})

            arm_specs = [(left, top), (top, right), (right, bottom), (bottom, left)]
            resistor_components = [c for c in component_types if c[1] == "resistor"]
            default_labels = ["R1", "R2", "R3", "R4"]
            for index, (p1, p2) in enumerate(arm_specs):
                comp_id = resistor_components[index][0] if index < len(resistor_components) else default_labels[index]
                mid_x, mid_y = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
                components.append({"id": comp_id, "type": "resistor", "x": mid_x, "y": mid_y, "label": comp_id})

            components.append({"id": "galvanometer", "type": "galvanometer", "x": 400, "y": 200, "label": "G"})
            connections.append({"from": list(left), "to": list(right), "type": "wire"})

            components.append({"id": "battery", "type": "battery", "x": 400, "y": 380, "label": "Battery"})
            connections.append({"from": list(bottom), "to": [400, 380], "type": "wire"})
            connections.append({"from": [400, 380], "to": list(top), "type": "wire"})
        else:
            left, right, top_y, bottom_y = 100.0, 700.0, 80.0, 320.0
            components.append({"id": "loop", "type": "wire_loop", "points": [[left, top_y], [right, top_y], [right, bottom_y], [left, bottom_y]]})

            non_battery = [c for c in component_types if c[1] != "battery"]
            if not non_battery:
                non_battery = [("R1", "resistor")]

            n = len(non_battery)
            for index, (comp_id, comp_type) in enumerate(non_battery, start=1):
                x = left + (right - left) * index / (n + 1)
                label = comp_id if comp_type == "resistor" else comp_type.capitalize()
                components.append({"id": comp_id, "type": comp_type, "x": x, "y": top_y, "label": label})

            components.append({"id": "battery", "type": "battery", "x": (left + right) / 2, "y": bottom_y, "label": "Battery"})

        return {
            "diagram_type": "circuit",
            "title": "Circuit Diagram",
            "canvas": dict(_CANVAS),
            "components": components,
            "connections": connections,
            "labels": [],
            "metadata": {
                "layout": "wheatstone_bridge" if is_bridge else "series_parallel",
                "component_count": len(components),
                "entities": entities or [],
                "scenario": scenario,
                "extra": extra,
            },
        }

    @classmethod
    def _generate_full_wave_rectifier(
        cls, entities: list[str] | None, scenario: str | None, extra: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Center-tapped full-wave rectifier: transformer secondary -> D1/D2 -> shared
        output node -> load resistor RL -> back to the center tap."""

        components: list[dict[str, Any]] = [
            {"id": "transformer", "type": "transformer", "x": 160, "y": 200, "label": "Transformer"},
            {"id": "diode_d1", "type": "diode", "x": 350, "y": 100, "label": "D1"},
            {"id": "diode_d2", "type": "diode", "x": 350, "y": 300, "label": "D2"},
            {"id": "load_resistor", "type": "resistor", "x": 570, "y": 200, "label": "RL"},
        ]
        connections: list[dict[str, Any]] = [
            {"from": [200, 100], "to": [320, 100], "type": "wire"},
            {"from": [380, 100], "to": [480, 100], "type": "wire"},
            {"from": [200, 300], "to": [320, 300], "type": "wire"},
            {"from": [380, 300], "to": [480, 300], "type": "wire"},
            {"from": [480, 100], "to": [480, 300], "type": "wire"},
            {"from": [480, 200], "to": [540, 200], "type": "wire"},
            {"from": [600, 200], "to": [640, 200], "type": "wire"},
            {"from": [200, 200], "to": [220, 200], "type": "wire"},
            {"from": [220, 200], "to": [220, 340], "type": "wire"},
            {"from": [220, 340], "to": [640, 340], "type": "wire"},
            {"from": [640, 340], "to": [640, 200], "type": "wire"},
        ]
        labels = [
            {"text": "AC Input", "x": 160, "y": 380, "anchor": "middle"},
            {"text": "DC Output (across RL)", "x": 570, "y": 270, "anchor": "middle"},
        ]

        return {
            "diagram_type": "circuit",
            "title": "Full Wave Rectifier (Center-Tapped)",
            "canvas": dict(_CANVAS),
            "components": components,
            "connections": connections,
            "labels": labels,
            "metadata": {
                "layout": "full_wave_rectifier_center_tapped",
                "component_count": len(components),
                "entities": entities or [],
                "scenario": scenario,
                "extra": extra or {},
            },
        }


_GRAPH_AXIS_PRESETS: list[tuple[list[str], str, str, str, str]] = [
    (["wheatstone", "v-i", "i-v", "potential difference", "current"], "Current (I)", "A", "Potential Difference (V)", "V"),
    (["capacitive reactance", "frequency"], "Frequency (f)", "Hz", "Capacitive Reactance (Xc)", "ohm"),
    (["magnetic field", "distance", "radius"], "Distance from wire (r)", "m", "Magnetic Field (B)", "T"),
    (["charge", "time"], "Time (t)", "s", "Charge (q)", "C"),
    (["current", "time"], "Time (t)", "s", "Current (I)", "A"),
    (["potential", "distance"], "Distance (x)", "m", "Electric Potential (V)", "V"),
]

# Maps the categorical "curve_shape" values that may appear in a physics
# analysis' ``extra`` block onto the curve-rendering ``curve_type`` values
# understood by the geometry code below.
_CURVE_SHAPE_MAP: dict[str, str] = {
    "linear": "linear",
    "linear_with_intercept": "linear_with_intercept",
    "non_linear": "non_linear",
    "saturation": "exponential_rise",
    "exponential_rise": "exponential_rise",
    "exponential_decay": "exponential_decay",
    "decay": "exponential_decay",
    "inverse_square": "non_linear",
}


class GraphDiagramGenerator:
    """Builds a labeled axes + curve specification for variation-type questions."""

    @classmethod
    def generate(
        cls,
        question_text: str,
        entities: list[str] | None = None,
        scenario: str | None = None,
        rules: dict[str, Any] | None = None,
        concept: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = question_text.lower()
        extra = extra or {}
        hint_text = " ".join([text, (scenario or "").lower(), " ".join(entities or []).lower()])

        if rules and rules.get("x_label") and rules.get("y_label"):
            x_label, x_unit = rules["x_label"], rules.get("x_unit", "")
            y_label, y_unit = rules["y_label"], rules.get("y_unit", "")
        elif extra.get("x_axis") and extra.get("y_axis"):
            x_label, x_unit = str(extra["x_axis"]).replace("_", " ").title(), ""
            y_label, y_unit = str(extra["y_axis"]).replace("_", " ").title(), ""
        else:
            for keywords, x_label, x_unit, y_label, y_unit in _GRAPH_AXIS_PRESETS:
                if all(keyword in hint_text for keyword in keywords):
                    break
            else:
                x_label, x_unit, y_label, y_unit = "Independent Variable", "", "Dependent Variable", ""

        rule_curve_type = (rules or {}).get("curve_type")
        extra_curve_shape = extra.get("curve_shape")
        if rule_curve_type:
            curve_type = rule_curve_type
        elif extra_curve_shape in _CURVE_SHAPE_MAP:
            curve_type = _CURVE_SHAPE_MAP[extra_curve_shape]
        else:
            curve_type = "linear"
            if _contains_any(hint_text, ["exponential", "decay", "charging", "discharging"]):
                curve_type = "exponential"
            elif _contains_any(hint_text, ["non-linear", "nonlinear", "diode", "characteristic"]):
                curve_type = "non_linear"

        decaying = curve_type == "exponential_decay" or _contains_any(hint_text, ["discharging", "decay"])
        has_intercept = curve_type == "linear_with_intercept"
        if curve_type in ("exponential_rise", "exponential_decay"):
            curve_type = "exponential"
        elif has_intercept:
            curve_type = "linear"

        origin = (100.0, 350.0)
        x_end = (750.0, 350.0)
        y_end = (100.0, 30.0)
        plot_width = x_end[0] - origin[0]
        plot_height = origin[1] - y_end[1]

        intercept_frac = 0.25 if has_intercept else 0.0

        points: list[list[float]] = []
        steps = 30
        for i in range(steps + 1):
            t = i / steps
            if curve_type == "exponential":
                frac = math.exp(-3 * t) if decaying else 1 - math.exp(-3 * t)
            elif curve_type == "non_linear":
                frac = t * t
            else:
                frac = t

            x = origin[0] + plot_width * (intercept_frac + (1 - intercept_frac) * t)
            y = origin[1] - plot_height * frac
            points.append([round(x, 1), round(y, 1)])

        components: list[dict[str, Any]] = [
            {"id": "x_axis", "type": "axis", "x1": origin[0], "y1": origin[1], "x2": x_end[0], "y2": x_end[1]},
            {"id": "y_axis", "type": "axis", "x1": origin[0], "y1": origin[1], "x2": y_end[0], "y2": y_end[1]},
            {"id": "curve_1", "type": "curve", "points": points, "label": curve_type},
        ]

        if has_intercept:
            intercept_x = origin[0] + plot_width * intercept_frac
            components.append(
                {"id": "threshold_marker", "type": "field_circle", "cx": intercept_x, "cy": origin[1], "radius": 4}
            )

        x_axis_text = f"{x_label} ({x_unit})" if x_unit else x_label
        y_axis_text = f"{y_label} ({y_unit})" if y_unit else y_label
        labels = [
            {"text": x_axis_text, "x": (origin[0] + x_end[0]) / 2, "y": origin[1] + 35, "anchor": "middle"},
            {"text": y_axis_text, "x": origin[0] - 60, "y": (origin[1] + y_end[1]) / 2, "anchor": "middle", "rotation": -90},
        ]

        title = "Graph"
        if extra.get("graph_type"):
            title = str(extra["graph_type"]).replace("_", " ").title()

        return {
            "diagram_type": "graph",
            "title": title,
            "canvas": dict(_CANVAS),
            "components": components,
            "connections": [],
            "labels": labels,
            "metadata": {
                "x_axis": {"label": x_label, "unit": x_unit},
                "y_axis": {"label": y_label, "unit": y_unit},
                "curve_type": curve_type,
                "entities": entities or [],
                "scenario": scenario,
                "extra": extra,
            },
        }


_RAY_OPTICAL_ELEMENTS: list[tuple[str, str, str]] = [
    ("compound microscope", "compound_microscope", "convex_lens"),
    ("telescope", "telescope", "convex_lens"),
    ("concave mirror", "concave_mirror", "concave_mirror"),
    ("convex mirror", "convex_mirror", "convex_mirror"),
    ("plane mirror", "plane_mirror", "plane_mirror"),
    ("concave lens", "concave_lens", "concave_lens"),
    ("convex lens", "convex_lens", "convex_lens"),
    ("prism", "prism", "convex_lens"),
]

# Maps a slugified optical element name (as might appear in a concept-extraction
# ``scenario``) directly to its render type, bypassing phrase search.
_ELEMENT_TO_RENDER: dict[str, str] = {_slugify(element): render for _, element, render in _RAY_OPTICAL_ELEMENTS}


_CONCEPT_TO_RENDER_TYPE: dict[str, str] = {
    "convex_lens": "convex_lens",
    "concave_lens": "concave_lens",
    "concave_mirror": "concave_mirror",
    "convex_mirror": "convex_mirror",
    "plane_mirror": "plane_mirror",
}

# Categorical object/image position -> distance from the optical element, in
# multiples of a fixed focal-length pixel unit. Used only by the rules-driven
# geometry engine (``rules`` is not None) - never by the LLM.
_POSITION_OFFSET_UNITS: dict[str, float] = {
    "beyond_2f": 2.6,
    "at_2f": 2.0,
    "between_f_and_2f": 1.5,
    "at_focus": 1.0,
    "between_lens_and_focus": 0.5,
    "any_position": 1.5,
}

# Categorical image size -> scale factor applied to the object's height.
_SIZE_FACTORS: dict[str, float] = {
    "diminished": 0.5,
    "same": 1.0,
    "magnified": 1.6,
    "highly_magnified": 2.4,
}

_FOCAL_UNIT = 80.0
_BASE_OBJECT_HEIGHT = 80.0

_IMAGE_NATURE_VALUES = ("real", "virtual")
_IMAGE_ORIENTATION_VALUES = ("erect", "inverted")


def _rules_from_extra(extra: dict[str, Any]) -> dict[str, Any]:
    """Build a synthetic ``rules`` dict from a physics analysis' ``extra`` block.

    Used when no template-driven ``scenario_rules`` are available - parses
    ``object_position`` and ``expected_image`` (e.g. ``"real_inverted_magnified"``)
    into the categorical ``object_position``/``image_nature``/``orientation``/
    ``size`` keys consumed by ``_generate_from_rules``.
    """

    rules: dict[str, Any] = {}

    object_position = extra.get("object_position")
    if isinstance(object_position, str) and object_position in _POSITION_OFFSET_UNITS:
        rules["object_position"] = object_position

    expected_image = extra.get("expected_image")
    if isinstance(expected_image, str):
        remaining = expected_image
        for size in sorted(_SIZE_FACTORS, key=len, reverse=True):
            if size in remaining:
                rules["size"] = size
                remaining = remaining.replace(size, "")
                break
        for nature in _IMAGE_NATURE_VALUES:
            if nature in remaining:
                rules["image_nature"] = nature
                remaining = remaining.replace(nature, "")
                break
        for orientation in _IMAGE_ORIENTATION_VALUES:
            if orientation in remaining:
                rules["orientation"] = orientation
                break

    return rules


class RayDiagramGenerator:
    """Builds a principal-axis + optical element + object/image ray diagram."""

    @classmethod
    def generate(
        cls,
        question_text: str,
        entities: list[str] | None = None,
        scenario: str | None = None,
        rules: dict[str, Any] | None = None,
        concept: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = question_text.lower()
        extra = extra or {}

        axis_y = 200.0
        element_x = 420.0

        effective_rules = rules or _rules_from_extra(extra)

        if effective_rules:
            optical_element = concept or "convex_lens"
            if optical_element not in _CONCEPT_TO_RENDER_TYPE:
                lens_type = extra.get("lens_type")
                mirror_type = extra.get("mirror_type")
                if lens_type:
                    optical_element = f"{lens_type}_lens"
                elif mirror_type:
                    optical_element = f"{mirror_type}_mirror"
            render_type = _CONCEPT_TO_RENDER_TYPE.get(optical_element, "convex_lens")
            components: list[dict[str, Any]] = [
                {"id": "principal_axis", "type": "axis", "x1": 60, "y1": axis_y, "x2": 740, "y2": axis_y},
                {
                    "id": "optical_element",
                    "type": render_type,
                    "x": element_x,
                    "y": axis_y,
                    "height": 240,
                    "label": optical_element.replace("_", " ").title(),
                },
            ]
            labels, image_components = cls._generate_from_rules(effective_rules, axis_y, element_x)
            components.extend(image_components)

            return {
                "diagram_type": "ray_diagram",
                "title": "Ray Diagram",
                "canvas": dict(_CANVAS),
                "components": components,
                "connections": [],
                "labels": labels,
                "metadata": {
                    "optical_element": optical_element,
                    "entities": entities or [],
                    "scenario": scenario,
                    "rules": effective_rules,
                    "extra": extra,
                },
            }

        # Legacy generic geometry (no physics-analyzer rules available).
        optical_element = "convex_lens"
        render_type = "convex_lens"

        scenario_key = _slugify(scenario) if scenario else ""
        if scenario_key in _ELEMENT_TO_RENDER:
            optical_element, render_type = scenario_key, _ELEMENT_TO_RENDER[scenario_key]
        else:
            for phrase, element, render in _RAY_OPTICAL_ELEMENTS:
                if phrase in text:
                    optical_element, render_type = element, render
                    break

        components = [
            {"id": "principal_axis", "type": "axis", "x1": 60, "y1": axis_y, "x2": 740, "y2": axis_y},
            {
                "id": "optical_element",
                "type": render_type,
                "x": element_x,
                "y": axis_y,
                "height": 240,
                "label": optical_element.replace("_", " ").title(),
            },
        ]

        is_mirror = render_type in {"concave_mirror", "convex_mirror", "plane_mirror"}

        object_x = 220.0
        object_height = 80.0
        components.append({"id": "object", "type": "object_arrow", "x": object_x, "y1": axis_y, "y2": axis_y - object_height, "label": "Object (O)"})

        if is_mirror:
            image_x = object_x + 60
            image_height = -100.0 if render_type == "concave_mirror" else 40.0
        else:
            image_x = element_x + 180
            image_height = -110.0 if render_type == "convex_lens" else 50.0

        image_y = axis_y - image_height
        components.append({"id": "image", "type": "image_arrow", "x": image_x, "y1": axis_y, "y2": image_y, "label": "Image (I)"})

        components.append(
            {
                "id": "ray_1",
                "type": "ray",
                "x1": object_x,
                "y1": axis_y - object_height,
                "x2": element_x,
                "y2": axis_y,
                "x3": image_x,
                "y3": image_y,
            }
        )
        components.append(
            {
                "id": "ray_2",
                "type": "ray",
                "x1": object_x,
                "y1": axis_y - object_height,
                "x2": element_x,
                "y2": axis_y - object_height * 0.3,
                "x3": image_x,
                "y3": image_y,
            }
        )

        return {
            "diagram_type": "ray_diagram",
            "title": "Ray Diagram",
            "canvas": dict(_CANVAS),
            "components": components,
            "connections": [],
            "labels": [],
            "metadata": {"optical_element": optical_element, "entities": entities or [], "scenario": scenario, "extra": extra},
        }

    @classmethod
    def _generate_from_rules(cls, rules: dict[str, Any], axis_y: float, element_x: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Categorical geometry engine: turns descriptive ``rules`` into object/image/ray components.

        ``rules`` carries only categorical attributes (``object_position``,
        ``image_side``, ``image_position``, ``image_nature``, ``orientation``,
        ``size``) - all pixel positions below are computed deterministically
        from those categories, never supplied by an LLM.
        """

        object_position = rules.get("object_position", "between_f_and_2f")
        image_side = rules.get("image_side", "opposite")
        image_position = rules.get("image_position", "between_f_and_2f")
        image_nature = rules.get("image_nature", "real")
        orientation = rules.get("orientation", "inverted")
        size = rules.get("size", "same")

        object_offset = _POSITION_OFFSET_UNITS.get(object_position, 1.5) * _FOCAL_UNIT
        object_x = element_x - object_offset
        object_height = _BASE_OBJECT_HEIGHT

        components: list[dict[str, Any]] = [
            {"id": "object", "type": "object_arrow", "x": object_x, "y1": axis_y, "y2": axis_y - object_height, "label": "Object (O)"}
        ]
        labels: list[dict[str, Any]] = []

        if image_position == "at_infinity":
            edge_x = _CANVAS["width"] - 20
            exit_y_1 = axis_y - object_height * 0.6
            exit_y_2 = axis_y - object_height * 0.3

            components.append(
                {
                    "id": "ray_1",
                    "type": "ray",
                    "x1": object_x,
                    "y1": axis_y - object_height,
                    "x2": element_x,
                    "y2": exit_y_1,
                    "x3": edge_x,
                    "y3": exit_y_1,
                }
            )
            components.append(
                {
                    "id": "ray_2",
                    "type": "ray",
                    "x1": object_x,
                    "y1": axis_y - object_height,
                    "x2": element_x,
                    "y2": exit_y_2,
                    "x3": edge_x,
                    "y3": exit_y_2,
                }
            )
            labels.append({"text": "Image at Infinity", "x": edge_x, "y": axis_y - object_height - 16, "anchor": "end"})
            return labels, components

        image_offset_units = _POSITION_OFFSET_UNITS.get(image_position, 1.5)
        if image_side == "same" and image_position == object_position:
            # Avoid overlapping the object when both fall in the same
            # categorical bracket on the same side of the optical element.
            image_offset_units += 0.3
        image_offset = image_offset_units * _FOCAL_UNIT
        image_x = element_x + image_offset if image_side == "opposite" else element_x - image_offset

        size_factor = _SIZE_FACTORS.get(size, 1.0)
        image_height_magnitude = object_height * size_factor
        image_height_signed = image_height_magnitude if orientation == "erect" else -image_height_magnitude
        image_y = axis_y - image_height_signed

        is_virtual = image_nature == "virtual"
        nature_text = "Virtual" if is_virtual else "Real"
        components.append(
            {
                "id": "image",
                "type": "image_arrow",
                "x": image_x,
                "y1": axis_y,
                "y2": image_y,
                "label": f"Image (I) - {nature_text}",
                "dashed": is_virtual,
            }
        )

        components.append(
            {
                "id": "ray_1",
                "type": "ray",
                "x1": object_x,
                "y1": axis_y - object_height,
                "x2": element_x,
                "y2": axis_y,
                "x3": image_x,
                "y3": image_y,
            }
        )
        components.append(
            {
                "id": "ray_2",
                "type": "ray",
                "x1": object_x,
                "y1": axis_y - object_height,
                "x2": element_x,
                "y2": axis_y - object_height * 0.3,
                "x3": image_x,
                "y3": image_y,
            }
        )

        return labels, components


_MAGNETIC_SOURCES: list[tuple[list[str], str]] = [
    (["solenoid"], "solenoid"),
    (["toroid"], "toroid"),
    (["circular loop", "current loop", "circular coil"], "circular_loop"),
    (["bar magnet"], "bar_magnet"),
    (["straight wire", "straight conductor", "long wire", "current carrying conductor", "current-carrying conductor"], "straight_wire"),
]


class MagneticFieldDiagramGenerator:
    """Builds a magnetic field-line specification for a given field source."""

    @classmethod
    def generate(
        cls,
        question_text: str,
        entities: list[str] | None = None,
        scenario: str | None = None,
        rules: dict[str, Any] | None = None,
        concept: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = question_text.lower()
        extra = extra or {}

        source = (rules or {}).get("source") or extra.get("source")
        if not source:
            source = "straight_wire"
            for keywords, source_type in _MAGNETIC_SOURCES:
                if any(keyword in text for keyword in keywords):
                    source = source_type
                    break

        cx, cy = 400.0, 200.0
        components: list[dict[str, Any]] = []

        if source == "straight_wire":
            components.append({"id": "wire", "type": "wire", "x1": cx, "y1": 40, "x2": cx, "y2": 360, "label": "I"})
            for radius in (50, 90, 130):
                components.append({"id": f"field_circle_{radius}", "type": "field_circle", "cx": cx, "cy": cy, "radius": radius})
        elif source == "solenoid":
            components.append({"id": "coil", "type": "solenoid", "x": cx - 150, "y": cy - 60, "width": 300, "height": 120, "turns": 8})
            for index, y in enumerate((cy - 30, cy, cy + 30)):
                components.append({"id": f"field_line_inside_{index}", "type": "field_arrow", "x1": cx - 150, "y1": y, "x2": cx + 150, "y2": y})
            components.append({"id": "field_line_outside", "type": "field_loop", "cx": cx, "cy": cy, "rx": 220, "ry": 150})
        elif source == "toroid":
            components.append({"id": "toroid_outer", "type": "field_circle", "cx": cx, "cy": cy, "radius": 130})
            components.append({"id": "toroid_inner", "type": "field_circle", "cx": cx, "cy": cy, "radius": 80})
            components.append({"id": "toroid_mid", "type": "field_circle", "cx": cx, "cy": cy, "radius": 105, "dashed": True})
        elif source == "circular_loop":
            components.append({"id": "loop", "type": "loop_edge", "cx": cx, "cy": cy, "rx": 140, "ry": 50})
            for index, (rx, ry) in enumerate([(80, 140), (110, 180), (140, 220)]):
                components.append({"id": f"field_line_{index}", "type": "field_loop", "cx": cx, "cy": cy, "rx": rx, "ry": ry})
        else:  # bar_magnet
            components.append({"id": "magnet_n", "type": "magnet_pole", "x": cx - 100, "y": cy - 40, "width": 100, "height": 80, "label": "N"})
            components.append({"id": "magnet_s", "type": "magnet_pole", "x": cx, "y": cy - 40, "width": 100, "height": 80, "label": "S"})
            for index, (rx, ry) in enumerate([(160, 80), (200, 110), (240, 140)]):
                components.append({"id": f"field_line_{index}", "type": "field_loop", "cx": cx, "cy": cy, "rx": rx, "ry": ry})

        labels = [{"text": source.replace("_", " ").title(), "x": cx, "y": 380, "anchor": "middle"}]

        return {
            "diagram_type": "magnetic_field",
            "title": "Magnetic Field Diagram",
            "canvas": dict(_CANVAS),
            "components": components,
            "connections": [],
            "labels": labels,
            "metadata": {"source": source, "entities": entities or [], "scenario": scenario, "extra": extra},
        }


DIAGRAM_GENERATORS = {
    "free_body": FreeBodyDiagramGenerator.generate,
    "circuit": CircuitDiagramGenerator.generate,
    "graph": GraphDiagramGenerator.generate,
    "ray_diagram": RayDiagramGenerator.generate,
    "magnetic_field": MagneticFieldDiagramGenerator.generate,
}
