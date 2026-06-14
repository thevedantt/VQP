"""Schemdraw-based circuit diagram rendering (PART 3).

Renders a simple series-loop circuit specification (as produced by
``CircuitDiagramGenerator``) to SVG using Schemdraw. Returns ``None`` for
unsupported layouts (e.g. Wheatstone bridge) or on any rendering failure, so
``diagram_svg.py`` can fall back to the existing custom SVG geometry engine.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import schemdraw
    import schemdraw.elements as elm

    SCHEMDRAW_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised when schemdraw is not installed
    SCHEMDRAW_AVAILABLE = False

_ELEMENT_MAP: dict[str, str] = {
    "battery": "SourceV",
    "resistor": "Resistor",
    "capacitor": "Capacitor",
    "inductor": "Inductor2",
    "diode": "Diode",
    "switch": "Switch",
    "ammeter": "MeterA",
    "voltmeter": "MeterV",
    "galvanometer": "MeterA",
    "rheostat": "Potentiometer",
    "transformer": "Transformer",
}


def render_circuit(spec: dict[str, Any]) -> str | None:
    """Render a series-loop circuit ``spec`` to an SVG string, or ``None`` to fall back."""

    if not SCHEMDRAW_AVAILABLE:
        return None

    metadata = spec.get("metadata", {})
    if metadata.get("layout") != "series_parallel":
        return None

    components = [c for c in spec.get("components", []) if c.get("type") != "wire_loop"]
    if not components:
        return None

    battery = next((c for c in components if c.get("type") == "battery"), None)
    others = [c for c in components if c.get("type") != "battery"]
    if not others:
        return None

    try:
        with schemdraw.Drawing(show=False) as d:
            d.config(unit=2.5, fontsize=11)
            for component in others:
                element_name = _ELEMENT_MAP.get(component.get("type", ""), "Resistor")
                element_cls = getattr(elm, element_name, elm.Resistor)
                d += element_cls().right().label(component.get("label", ""))

            d.push()
            d += elm.Line().down()
            if battery is not None:
                d += elm.SourceV().left().reverse().label(battery.get("label", "Battery"))
            else:
                d += elm.Line().left()
            d += elm.Line().up()
            d.pop()

        svg_bytes = d.get_imagedata("svg")
        return svg_bytes.decode("utf-8")
    except Exception as exc:  # pragma: no cover - depends on schemdraw runtime
        logger.warning("Schemdraw circuit rendering failed, falling back to custom SVG: %s", exc)
        return None
