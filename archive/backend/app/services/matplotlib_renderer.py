"""Matplotlib-based graph diagram rendering (PART 3).

Renders the curve specification produced by ``GraphDiagramGenerator`` to SVG
using Matplotlib, with labeled axes derived from the specification's
metadata. Returns ``None`` on any rendering failure so ``diagram_svg.py`` can
fall back to the existing custom SVG geometry engine.

Uses ``matplotlib.figure.Figure`` + ``FigureCanvasSVG`` directly (no
``pyplot``/GUI backend involved), so it is safe to call from a headless
server process.
"""

from __future__ import annotations

import io
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from matplotlib.backends.backend_svg import FigureCanvasSVG
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised when matplotlib is not installed
    MATPLOTLIB_AVAILABLE = False


def render_graph(spec: dict[str, Any]) -> str | None:
    """Render a graph ``spec`` (axes + curve) to an SVG string, or ``None`` to fall back."""

    if not MATPLOTLIB_AVAILABLE:
        return None

    components = spec.get("components", [])
    curve = next((c for c in components if c.get("type") == "curve"), None)
    points = curve.get("points") if curve else None
    if not points:
        return None

    try:
        canvas = spec.get("canvas", {})
        height = canvas.get("height", 400)

        xs = [p[0] for p in points]
        ys = [height - p[1] for p in points]

        metadata = spec.get("metadata", {})
        x_meta = metadata.get("x_axis", {})
        y_meta = metadata.get("y_axis", {})
        x_label = x_meta.get("label", "")
        x_unit = x_meta.get("unit", "")
        y_label = y_meta.get("label", "")
        y_unit = y_meta.get("unit", "")
        x_text = f"{x_label} ({x_unit})" if x_unit else x_label
        y_text = f"{y_label} ({y_unit})" if y_unit else y_label

        fig = Figure(figsize=(6.4, 3.4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(xs, ys, color="#2563eb", linewidth=2.5)
        ax.set_xlabel(x_text)
        ax.set_ylabel(y_text)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()

        buf = io.StringIO()
        FigureCanvasSVG(fig).print_svg(buf)
        return buf.getvalue()
    except Exception as exc:  # pragma: no cover - depends on matplotlib runtime
        logger.warning("Matplotlib graph rendering failed, falling back to custom SVG: %s", exc)
        return None
