"""DefaultTheme — neutral styling suitable for general scientific diagrams."""

from visualq_diagram_engine.theme.base_theme import BaseTheme


class DefaultTheme(BaseTheme):
    """
    A neutral, clean styling for non-textbook scientific diagrams.
    Slightly heavier strokes and larger fonts than NCERTTheme
    for screen/presentation use.
    """

    font_size_title   = 18.0
    font_size_region  = 20.0
    font_size_label   = 13.0
    font_size_caption = 12.0
    font_size_ion     = 17.0
    font_size_field   = 12.0

    stroke_width_border   = 2.0
    stroke_width_wire     = 1.8
    stroke_width_field    = 1.4
    stroke_width_boundary = 1.2

    color_p_tint   = "#FFF0F0"
    color_n_tint   = "#F0F0FF"
    color_dep_fill = "#EBEBEB"

    hole_radius     = 10.0
    electron_radius = 8.0
    carrier_margin  = 28.0

    canvas_width  = 960.0
    canvas_height = 520.0
