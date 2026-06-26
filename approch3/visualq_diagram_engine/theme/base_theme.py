"""BaseTheme — abstract styling contract for all diagram renderers."""

from __future__ import annotations
from abc import ABC


class BaseTheme(ABC):
    """
    Every theme subclass defines a set of named constants.
    The renderer, layout engine, and symbol library read these
    instead of embedding literal values.

    Themes are plain classes with class-level float/int/str attributes —
    no instances needed. Read with NCERTTheme.wire_stroke_width, not instantiated.
    """

    # ── Canvas ────────────────────────────────────────────────────────────────
    background: str = "#FFFFFF"
    canvas_width: float  = 900.0
    canvas_height: float = 480.0

    # ── Typography ────────────────────────────────────────────────────────────
    font_family: str      = "Arial"
    font_size_title: float   = 16.0
    font_size_region: float  = 18.0
    font_size_label: float   = 11.0
    font_size_caption: float = 10.0
    font_size_ion: float     = 16.0
    font_size_field: float   = 10.0
    font_size_component: float = 11.0
    font_size_small: float   = 9.0

    # ── Strokes ───────────────────────────────────────────────────────────────
    stroke_default: str    = "#000000"
    stroke_width_border: float = 1.5   # semiconductor body
    stroke_width_wire: float   = 1.4   # circuit wires + components
    stroke_width_field: float  = 1.1   # field arrows
    stroke_width_boundary: float = 1.0 # dashed depletion boundaries

    # ── Colors ────────────────────────────────────────────────────────────────
    color_p_tint: str     = "#FFF9F9"
    color_n_tint: str     = "#F8F8FF"
    color_dep_fill: str   = "#F2F2F2"
    color_label: str      = "#000000"
    color_caption: str    = "#333333"
    color_boundary: str   = "#444444"
    color_field: str      = "#222222"
    color_ion: str        = "#111111"

    # ── Dashes ────────────────────────────────────────────────────────────────
    dash_boundary: str  = "5,4"

    # ── Carriers ─────────────────────────────────────────────────────────────
    hole_radius: float        = 8.0
    electron_radius: float    = 7.0
    carrier_arrow_length: float = 18.0
    carrier_spacing_x: float  = 58.0
    carrier_spacing_y: float  = 46.0
    carrier_margin: float     = 30.0
    carrier_rows: int         = 3
    carrier_cols: int         = 3

    # ── Ions ─────────────────────────────────────────────────────────────────
    ion_rows: int         = 3
    ion_cols: int         = 1
    ion_spacing_y: float  = 44.0

    # ── Field arrows ─────────────────────────────────────────────────────────
    field_arrow_head_size: float  = 6.0
    field_arrow_label_offset: float = 11.0
    field_e_y_fraction: float   = 0.35   # vertical position of E arrow
    field_ei_y_fraction: float  = 0.65   # vertical position of Ei arrow
    field_e_x_margin: float     = 14.0   # margin from region edge
    field_ei_x_margin: float    = 10.0   # margin from depletion edge

    # ── Layout ────────────────────────────────────────────────────────────────
    semi_margin_x: float    = 85.0
    semi_margin_y: float    = 75.0
    semi_height: float      = 165.0
    semi_p_frac: float      = 0.40
    semi_dep_frac: float    = 0.14
    semi_n_frac: float      = 0.46
    circuit_gap: float      = 50.0      # gap between semiconductor bottom and circuit rail
    circuit_arm_margin: float = 42.0
    switch_length: float    = 55.0
    battery_gap: float      = 18.0
    resistor_length: float  = 80.0
    label_top_offset: float = -13.0     # label above region top
    label_bottom_offset: float = 14.0   # label below region bottom
    title_y: float          = 30.0
    caption_bottom_margin: float = 18.0

    @classmethod
    def wire_style(cls) -> dict:
        return {"stroke": cls.stroke_default, "stroke_width": cls.stroke_width_wire}

    @classmethod
    def field_style(cls) -> dict:
        return {
            "stroke": cls.color_field,
            "stroke_width": cls.stroke_width_field,
            "fill": cls.color_field,
            "font_size": cls.font_size_field,
            "font_family": cls.font_family,
            "text_anchor": "middle",
        }

    @classmethod
    def ion_style(cls) -> dict:
        return {
            "fill": cls.color_ion,
            "stroke": "none",
            "font_size": cls.font_size_ion,
            "font_weight": "bold",
            "font_family": cls.font_family,
            "text_anchor": "middle",
        }
