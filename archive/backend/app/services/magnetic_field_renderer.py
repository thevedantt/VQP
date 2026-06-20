"""Magpylib-backed magnetic field rendering (Phase 5).

Computes the magnetic field via real Biot-Savart calculations (Magpylib) for
the render schema produced by ``magnetic_field_engine``, draws field-line
streamplots with matplotlib, and exports SVG.

Follows the "bypass renderer" pattern established by
``schemdraw_renderer.py``: ``render`` returns ``None`` on any
failure/unsupported case so ``DiagramRouter`` can fall back to the legacy
hand-rolled SVG generator.
"""

from __future__ import annotations

import logging
from io import StringIO
from typing import Any

logger = logging.getLogger(__name__)

try:
    import matplotlib

    matplotlib.use("Agg")
    import numpy as np
    from matplotlib import pyplot as plt
    from matplotlib.patches import Rectangle

    import magpylib as magpy

    MAGPYLIB_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised when magpylib/matplotlib aren't installed
    MAGPYLIB_AVAILABLE = False


def render(render_schema: dict[str, Any]) -> str | None:
    """Render a magnetic_field render schema to an SVG string, or ``None`` to fall back."""

    if not MAGPYLIB_AVAILABLE:
        return None

    model = render_schema.get("metadata", {}).get("magpylib_model")
    if not model:
        return None

    source_type = model.get("source_type")
    current_sign = 1 if model.get("current_sign", 1) >= 0 else -1
    title = render_schema.get("title", "Magnetic Field")

    try:
        if source_type in ("circular_loop", "toroid"):
            fig = _draw_circular_loop(title, current_sign)
        elif source_type == "solenoid":
            fig = _draw_solenoid(title, current_sign, model.get("turns", 8))
        elif source_type == "straight_wire":
            fig = _draw_straight_wire(title, current_sign)
        elif source_type == "bar_magnet":
            fig = _draw_bar_magnet(title, model.get("pole_orientation", "n_right"))
        else:
            return None

        buf = StringIO()
        fig.savefig(buf, format="svg", bbox_inches="tight")
        plt.close(fig)
        return buf.getvalue()
    except Exception as exc:  # pragma: no cover - depends on magpylib/matplotlib runtime
        logger.warning("Magpylib magnetic field rendering failed, falling back to legacy SVG: %s", exc)
        return None


def _new_axes(title: str, half_extent: float) -> tuple[Any, Any]:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.set_xlim(-half_extent, half_extent)
    ax.set_ylim(-half_extent, half_extent)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig, ax


def _streamplot_field(ax: Any, source: Any, plane: str, half_extent: float, n: int = 28) -> None:
    """Compute B via Magpylib on a grid and draw normalized field-line streamlines."""

    coords = np.linspace(-half_extent, half_extent, n)
    a, b = np.meshgrid(coords, coords)
    if plane == "xz":
        points = np.stack([a, np.zeros_like(a), b], axis=-1)
    else:  # xy
        points = np.stack([a, b, np.zeros_like(a)], axis=-1)

    field = source.getB(points)
    if plane == "xz":
        u, v = field[..., 0], field[..., 2]
    else:
        u, v = field[..., 0], field[..., 1]

    magnitude = np.hypot(u, v)
    safe = np.isfinite(magnitude) & (magnitude > 1e-12)
    u_norm = np.zeros_like(u)
    v_norm = np.zeros_like(v)
    u_norm[safe] = u[safe] / magnitude[safe]
    v_norm[safe] = v[safe] / magnitude[safe]

    ax.streamplot(a, b, u_norm, v_norm, density=1.2, color="#2563eb", linewidth=1, arrowsize=1.2)


def _draw_circular_loop(title: str, current_sign: int) -> Any:
    radius = 2.0
    loop = magpy.current.Circle(current=current_sign * 1.0, diameter=2 * radius)

    fig, ax = _new_axes(title, half_extent=5.0)
    _streamplot_field(ax, loop, plane="xz", half_extent=5.0)

    # Cross-section of the ring at x = +-radius: current flows in opposite
    # directions through the page on each side.
    near_marker, far_marker = ("o", "x") if current_sign >= 0 else ("x", "o")
    ax.plot(radius, 0, marker=near_marker, color="black", markersize=10, markeredgewidth=2)
    ax.plot(-radius, 0, marker=far_marker, color="black", markersize=10, markeredgewidth=2)
    ax.text(radius, 0.4, "I", ha="center")
    ax.text(-radius, 0.4, "I", ha="center")

    return fig


def _draw_solenoid(title: str, current_sign: int, turns: int) -> Any:
    turns = max(2, min(int(turns or 8), 16))
    length = 4.0
    radius = 1.5
    half_extent = 6.0

    sources = magpy.Collection(
        *[
            magpy.current.Circle(current=current_sign * 1.0, diameter=2 * radius, position=(0, 0, z))
            for z in np.linspace(-length / 2, length / 2, turns)
        ]
    )

    fig, ax = _new_axes(title, half_extent=half_extent)
    _streamplot_field(ax, sources, plane="xz", half_extent=half_extent)

    ax.add_patch(Rectangle((-radius, -length / 2), 2 * radius, length, fill=False, edgecolor="#1f2937", linewidth=2))
    for z in np.linspace(-length / 2, length / 2, turns):
        ax.plot([-radius, radius], [z, z], color="#1f2937", linewidth=1)

    return fig


def _draw_straight_wire(title: str, current_sign: int) -> Any:
    half_extent = 4.0
    wire = magpy.current.Polyline(current=current_sign * 1.0, vertices=[(0, 0, -5), (0, 0, 5)])

    fig, ax = _new_axes(title, half_extent=half_extent)
    _streamplot_field(ax, wire, plane="xy", half_extent=half_extent)

    # out_of_page (sign +1) -> dot, into_page (sign -1) -> cross.
    marker = "o" if current_sign >= 0 else "x"
    ax.plot(0, 0, marker=marker, color="black", markersize=12, markeredgewidth=2)
    ax.text(0.3, 0.3, "I", ha="left")

    return fig


def _draw_bar_magnet(title: str, pole_orientation: str) -> Any:
    half_extent = 6.0
    n_on_right = pole_orientation not in ("n_left", "horizontal_n_left")
    polarization = (1.0, 0.0, 0.0) if n_on_right else (-1.0, 0.0, 0.0)
    magnet = magpy.magnet.Cuboid(polarization=polarization, dimension=(4, 2, 1.5))

    fig, ax = _new_axes(title, half_extent=half_extent)
    _streamplot_field(ax, magnet, plane="xz", half_extent=half_extent)

    ax.add_patch(Rectangle((-2, -0.75), 4, 1.5, fill=False, edgecolor="#1f2937", linewidth=2))
    n_x, s_x = (2, -2) if n_on_right else (-2, 2)
    ax.text(n_x, 0, "N", ha="center", va="center", fontsize=14, fontweight="bold", color="#ef4444")
    ax.text(s_x, 0, "S", ha="center", va="center", fontsize=14, fontweight="bold", color="#3b82f6")

    return fig
