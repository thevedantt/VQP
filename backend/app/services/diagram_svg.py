"""SVG generation layer.

Converts the structured diagram specifications produced by
``diagram_generators.py`` (``canvas`` / ``components`` / ``connections`` /
``labels``) into ready-to-render SVG markup strings.
"""

from __future__ import annotations

from html import escape as _esc
from typing import Any

_ARROW_DEFS = (
    '<defs>'
    '<marker id="arrow-dark" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" '
    'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 Z" fill="#1f2937"/></marker>'
    '<marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" '
    'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 Z" fill="#dc2626"/></marker>'
    '<marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" '
    'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 Z" fill="#2563eb"/></marker>'
    '</defs>'
)

_STROKE_COLORS = {"dark": "#1f2937", "red": "#dc2626", "blue": "#2563eb"}
_MARKERS = {"dark": "arrow-dark", "red": "arrow-red", "blue": "arrow-blue"}


def _wrap_svg(canvas: dict[str, Any], parts: list[str]) -> str:
    width, height = canvas.get("width", 800), canvas.get("height", 400)
    body = "".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="Arial, sans-serif" font-size="14">'
        f"{_ARROW_DEFS}{body}</svg>"
    )


def _rect(x: float, y: float, width: float, height: float, fill: str = "none", stroke: str = "#1f2937", stroke_width: float = 2, opacity: float | None = None) -> str:
    opacity_attr = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{opacity_attr} />'


def _line(x1: float, y1: float, x2: float, y2: float, stroke: str = "#1f2937", stroke_width: float = 2, dashed: bool = False) -> str:
    dash_attr = ' stroke-dasharray="5 5"' if dashed else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr} />'


def _arrow(x1: float, y1: float, x2: float, y2: float, color: str = "dark") -> str:
    stroke = _STROKE_COLORS.get(color, "#1f2937")
    marker = _MARKERS.get(color, "arrow-dark")
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="2" marker-end="url(#{marker})" />'


def _text(x: float, y: float, text: str, anchor: str = "start", dy: float = 0, fill: str = "#1f2937", font_weight: str = "normal", rotation: float | None = None) -> str:
    if not text:
        return ""
    transform_attr = f' transform="rotate({rotation} {x} {y})"' if rotation else ""
    return f'<text x="{x}" y="{y + dy}" text-anchor="{anchor}" fill="{fill}" font-weight="{font_weight}"{transform_attr}>{_esc(str(text))}</text>'


def _polygon(points: list[list[float]], fill: str = "none", stroke: str = "#1f2937", stroke_width: float = 2) -> str:
    points_str = " ".join(f"{p[0]},{p[1]}" for p in points)
    return f'<polygon points="{points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'


def _polyline(points: list[list[float]], stroke: str = "#1f2937", stroke_width: float = 2, dashed: bool = False) -> str:
    points_str = " ".join(f"{p[0]},{p[1]}" for p in points)
    dash_attr = ' stroke-dasharray="6 4"' if dashed else ""
    return f'<polyline points="{points_str}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr} />'


def _render_free_body(spec: dict[str, Any]) -> str:
    parts: list[str] = []
    for c in spec["components"]:
        t = c["type"]
        if t == "incline":
            parts.append(_polygon(c["points"], fill="#e5e7eb"))
        elif t == "ground":
            parts.append(_line(c["x1"], c["y1"], c["x2"], c["y2"], stroke_width=3))
        elif t == "box":
            cx, cy = c["x"] + c["width"] / 2, c["y"] + c["height"] / 2
            group = _rect(c["x"], c["y"], c["width"], c["height"], fill="#bfdbfe", stroke_width=2) + _text(cx, cy, c.get("label", ""), anchor="middle", dy=5, font_weight="bold")
            if c.get("rotation"):
                parts.append(f'<g transform="rotate({c["rotation"]} {cx} {cy})">{group}</g>')
            else:
                parts.append(group)
        elif t == "arrow":
            parts.append(_arrow(c["x1"], c["y1"], c["x2"], c["y2"], color="red"))
            parts.append(_text(c["x2"], c["y2"], c.get("label", ""), anchor="middle", dy=-8, font_weight="bold"))
    for label in spec.get("labels", []):
        parts.append(_text(label["x"], label["y"], label["text"], anchor=label.get("anchor", "start")))
    return _wrap_svg(spec["canvas"], parts)


def _circuit_symbol(c: dict[str, Any]) -> str:
    t = c["type"]
    x, y, label = c.get("x", 0), c.get("y", 0), c.get("label", "")
    bg = _rect(x - 32, y - 16, 64, 32, fill="white", stroke="none")

    if t == "battery":
        body = _line(x - 8, y - 16, x - 8, y + 16, stroke_width=2) + _line(x + 8, y - 8, x + 8, y + 8, stroke_width=5)
    elif t in ("ammeter", "voltmeter", "galvanometer"):
        letter = {"ammeter": "A", "voltmeter": "V", "galvanometer": "G"}[t]
        body = f'<circle cx="{x}" cy="{y}" r="16" fill="white" stroke="#1f2937" stroke-width="2" />' + _text(x, y, letter, anchor="middle", dy=5, font_weight="bold")
    elif t == "capacitor":
        body = _line(x - 6, y - 16, x - 6, y + 16, stroke_width=2) + _line(x + 6, y - 16, x + 6, y + 16, stroke_width=2)
    elif t == "switch":
        body = (
            _line(x - 22, y, x - 8, y, stroke_width=2)
            + _line(x - 8, y, x + 16, y - 14, stroke_width=2)
            + _line(x + 22, y, x + 8, y, stroke_width=2)
            + f'<circle cx="{x - 8}" cy="{y}" r="3" fill="#1f2937" />'
            + f'<circle cx="{x + 8}" cy="{y}" r="3" fill="#1f2937" />'
        )
    elif t == "rheostat":
        body = _rect(x - 28, y - 8, 56, 16, stroke_width=2) + _arrow(x - 24, y + 22, x + 24, y - 22, "dark")
    else:  # resistor and fallback
        body = _rect(x - 28, y - 12, 56, 24, fill="white", stroke_width=2)

    return bg + body + _text(x, y + 34, label, anchor="middle")


def _render_circuit(spec: dict[str, Any]) -> str:
    parts: list[str] = []
    for c in spec["components"]:
        if c["type"] == "wire_loop":
            parts.append(_polygon(c["points"]))
        else:
            parts.append(_circuit_symbol(c))
    for conn in spec.get("connections", []):
        f, to = conn["from"], conn["to"]
        parts.append(_line(f[0], f[1], to[0], to[1]))
    for label in spec.get("labels", []):
        parts.append(_text(label["x"], label["y"], label["text"], anchor=label.get("anchor", "start")))
    return _wrap_svg(spec["canvas"], parts)


def _render_graph(spec: dict[str, Any]) -> str:
    parts: list[str] = []
    for c in spec["components"]:
        if c["type"] == "axis":
            parts.append(_arrow(c["x1"], c["y1"], c["x2"], c["y2"], color="dark"))
        elif c["type"] == "curve":
            parts.append(_polyline(c["points"], stroke="#2563eb", stroke_width=2.5))
    for label in spec.get("labels", []):
        parts.append(_text(label["x"], label["y"], label["text"], anchor=label.get("anchor", "start"), rotation=label.get("rotation")))
    return _wrap_svg(spec["canvas"], parts)


def _optical_element_svg(c: dict[str, Any]) -> str:
    x, y, h, t = c["x"], c["y"], c["height"], c["type"]
    half = h / 2
    parts: list[str] = []

    if t == "convex_lens":
        parts.append(_line(x, y - half, x, y + half, stroke_width=3))
        parts.append(_polygon([[x - 10, y - half + 16], [x + 10, y - half + 16], [x, y - half]], fill="#1f2937"))
        parts.append(_polygon([[x - 10, y + half - 16], [x + 10, y + half - 16], [x, y + half]], fill="#1f2937"))
    elif t == "concave_lens":
        parts.append(_line(x, y - half, x, y + half, stroke_width=3))
        parts.append(_polygon([[x - 10, y - half], [x + 10, y - half], [x, y - half + 16]], fill="#1f2937"))
        parts.append(_polygon([[x - 10, y + half], [x + 10, y + half], [x, y + half - 16]], fill="#1f2937"))
    elif t == "plane_mirror":
        parts.append(_line(x, y - half, x, y + half, stroke_width=3))
        for i in range(8):
            yy = y - half + i * (h / 7)
            parts.append(_line(x, yy, x + 8, yy + 6, stroke_width=1))
    elif t == "concave_mirror":
        parts.append(f'<path d="M {x + 30} {y - half} Q {x - 20} {y} {x + 30} {y + half}" fill="none" stroke="#1f2937" stroke-width="3" />')
    elif t == "convex_mirror":
        parts.append(f'<path d="M {x - 30} {y - half} Q {x + 20} {y} {x - 30} {y + half}" fill="none" stroke="#1f2937" stroke-width="3" />')

    parts.append(_text(x, y + half + 20, c.get("label", ""), anchor="middle"))
    return "".join(parts)


def _render_ray_diagram(spec: dict[str, Any]) -> str:
    parts: list[str] = []
    for c in spec["components"]:
        t = c["type"]
        if t == "axis":
            parts.append(_line(c["x1"], c["y1"], c["x2"], c["y2"], stroke="#9ca3af", stroke_width=1.5, dashed=True))
        elif t in ("convex_lens", "concave_lens", "concave_mirror", "convex_mirror", "plane_mirror"):
            parts.append(_optical_element_svg(c))
        elif t in ("object_arrow", "image_arrow"):
            color = "red" if t == "object_arrow" else "blue"
            parts.append(_arrow(c["x"], c["y1"], c["x"], c["y2"], color=color))
            label_y = c["y2"] - 8 if c["y2"] < c["y1"] else c["y2"] + 18
            parts.append(_text(c["x"], label_y, c.get("label", ""), anchor="middle"))
        elif t == "ray":
            parts.append(_polyline([[c["x1"], c["y1"]], [c["x2"], c["y2"]], [c["x3"], c["y3"]]], stroke="#f97316", stroke_width=1.5, dashed=True))
    return _wrap_svg(spec["canvas"], parts)


def _render_magnetic_field(spec: dict[str, Any]) -> str:
    parts: list[str] = []
    for c in spec["components"]:
        t = c["type"]
        if t == "wire":
            parts.append(_line(c["x1"], c["y1"], c["x2"], c["y2"], stroke_width=4))
            parts.append(_text(c["x1"] + 10, c["y1"] + 20, c.get("label", ""), anchor="start"))
        elif t == "field_circle":
            parts.append(f'<circle cx="{c["cx"]}" cy="{c["cy"]}" r="{c["radius"]}" fill="none" stroke="#2563eb" stroke-width="1.5"' + (' stroke-dasharray="4 4"' if c.get("dashed") else "") + " />")
        elif t == "solenoid":
            parts.append(_rect(c["x"], c["y"], c["width"], c["height"], stroke_width=2))
            turns = c.get("turns", 8)
            for i in range(turns + 1):
                tx = c["x"] + i * (c["width"] / turns)
                parts.append(_line(tx, c["y"], tx, c["y"] + c["height"], stroke_width=1))
        elif t == "field_arrow":
            parts.append(_arrow(c["x1"], c["y1"], c["x2"], c["y2"], color="blue"))
        elif t == "field_loop":
            parts.append(f'<ellipse cx="{c["cx"]}" cy="{c["cy"]}" rx="{c["rx"]}" ry="{c["ry"]}" fill="none" stroke="#2563eb" stroke-width="1.5" stroke-dasharray="5 5" />')
        elif t == "loop_edge":
            parts.append(f'<ellipse cx="{c["cx"]}" cy="{c["cy"]}" rx="{c["rx"]}" ry="{c["ry"]}" fill="none" stroke="#1f2937" stroke-width="3" />')
        elif t == "magnet_pole":
            color = "#ef4444" if c.get("label") == "N" else "#3b82f6"
            parts.append(_rect(c["x"], c["y"], c["width"], c["height"], fill=color, stroke_width=2, opacity=0.7))
            parts.append(_text(c["x"] + c["width"] / 2, c["y"] + c["height"] / 2, c.get("label", ""), anchor="middle", dy=6, fill="white", font_weight="bold"))
    for label in spec.get("labels", []):
        parts.append(_text(label["x"], label["y"], label["text"], anchor=label.get("anchor", "start")))
    return _wrap_svg(spec["canvas"], parts)


_RENDERERS = {
    "free_body": _render_free_body,
    "circuit": _render_circuit,
    "graph": _render_graph,
    "ray_diagram": _render_ray_diagram,
    "magnetic_field": _render_magnetic_field,
}


def render_svg(specification: dict[str, Any]) -> str:
    """Render a structured diagram specification into an SVG markup string.

    Returns an empty string for unsupported/unknown diagram types so callers
    can degrade gracefully rather than failing the whole request.
    """

    renderer = _RENDERERS.get(specification.get("diagram_type", ""))
    if renderer is None:
        return ""
    return renderer(specification)
