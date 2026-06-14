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
    def generate(cls, question_text: str, entities: list[str] | None = None, scenario: str | None = None) -> dict[str, Any]:
        text = question_text.lower()

        on_incline = _contains_any(text, ["incline", "inclined plane", "slope", "ramp"])
        has_friction = _contains_any(text, ["friction"])
        has_tension = _contains_any(text, ["tension", "string", "rope", "wire is attached", "pulley"])
        has_applied_force = _contains_any(text, ["applied force", "force f", "pushed", "pulled", "push", "pull"])

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
    def generate(cls, question_text: str, entities: list[str] | None = None, scenario: str | None = None) -> dict[str, Any]:
        text = question_text.lower()

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

        is_bridge = _contains_any(text, ["wheatstone bridge", "meter bridge"])

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


class GraphDiagramGenerator:
    """Builds a labeled axes + curve specification for variation-type questions."""

    @classmethod
    def generate(cls, question_text: str, entities: list[str] | None = None, scenario: str | None = None) -> dict[str, Any]:
        text = question_text.lower()
        hint_text = " ".join([text, (scenario or "").lower(), " ".join(entities or []).lower()])

        for keywords, x_label, x_unit, y_label, y_unit in _GRAPH_AXIS_PRESETS:
            if all(keyword in hint_text for keyword in keywords):
                break
        else:
            x_label, x_unit, y_label, y_unit = "Independent Variable", "", "Dependent Variable", ""

        curve_type = "linear"
        if _contains_any(hint_text, ["exponential", "decay", "charging", "discharging"]):
            curve_type = "exponential"
        elif _contains_any(hint_text, ["non-linear", "nonlinear", "diode", "characteristic"]):
            curve_type = "non_linear"

        decaying = _contains_any(hint_text, ["discharging", "decay"])

        origin = (100.0, 350.0)
        x_end = (750.0, 350.0)
        y_end = (100.0, 30.0)
        plot_width = x_end[0] - origin[0]
        plot_height = origin[1] - y_end[1]

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

            x = origin[0] + plot_width * t
            y = origin[1] - plot_height * frac
            points.append([round(x, 1), round(y, 1)])

        components: list[dict[str, Any]] = [
            {"id": "x_axis", "type": "axis", "x1": origin[0], "y1": origin[1], "x2": x_end[0], "y2": x_end[1]},
            {"id": "y_axis", "type": "axis", "x1": origin[0], "y1": origin[1], "x2": y_end[0], "y2": y_end[1]},
            {"id": "curve_1", "type": "curve", "points": points, "label": curve_type},
        ]

        x_axis_text = f"{x_label} ({x_unit})" if x_unit else x_label
        y_axis_text = f"{y_label} ({y_unit})" if y_unit else y_label
        labels = [
            {"text": x_axis_text, "x": (origin[0] + x_end[0]) / 2, "y": origin[1] + 35, "anchor": "middle"},
            {"text": y_axis_text, "x": origin[0] - 60, "y": (origin[1] + y_end[1]) / 2, "anchor": "middle", "rotation": -90},
        ]

        return {
            "diagram_type": "graph",
            "title": "Graph",
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


class RayDiagramGenerator:
    """Builds a principal-axis + optical element + object/image ray diagram."""

    @classmethod
    def generate(cls, question_text: str, entities: list[str] | None = None, scenario: str | None = None) -> dict[str, Any]:
        text = question_text.lower()

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

        axis_y = 200.0
        element_x = 420.0

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
            "metadata": {"optical_element": optical_element, "entities": entities or [], "scenario": scenario},
        }


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
    def generate(cls, question_text: str, entities: list[str] | None = None, scenario: str | None = None) -> dict[str, Any]:
        text = question_text.lower()

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
            "metadata": {"source": source, "entities": entities or [], "scenario": scenario},
        }


DIAGRAM_GENERATORS = {
    "free_body": FreeBodyDiagramGenerator.generate,
    "circuit": CircuitDiagramGenerator.generate,
    "graph": GraphDiagramGenerator.generate,
    "ray_diagram": RayDiagramGenerator.generate,
    "magnetic_field": MagneticFieldDiagramGenerator.generate,
}
