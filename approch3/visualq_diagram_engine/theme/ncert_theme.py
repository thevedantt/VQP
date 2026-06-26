"""NCERTTheme — styling matching NCERT Class 12 Physics textbook illustrations."""

from visualq_diagram_engine.theme.base_theme import BaseTheme


class NCERTTheme(BaseTheme):
    """
    NCERT Class 12 Physics textbook illustration style.

    Characteristics:
    - Monochrome line art with very light region tints
    - Arial font throughout
    - Thin, consistent strokes (1.0–1.5 px)
    - No decorative fills, no gradients, no shadows
    - Plain hollow circles for holes, solid black for electrons
    - Standard circuit symbols (rectangular resistor, horizontal battery cells)
    - Small, legible labels directly adjacent to components
    """

    background = "#FFFFFF"
    font_family = "Arial"

    # Typography — strictly sized for textbook readability at A4 print scale
    font_size_title   = 16.0
    font_size_region  = 18.0
    font_size_label   = 11.0
    font_size_caption = 10.0
    font_size_ion     = 16.0
    font_size_field   = 10.0
    font_size_small   = 9.0

    # Colors — near-black ink, very light region tints
    color_p_tint    = "#FFF9F9"
    color_n_tint    = "#F8F8FF"
    color_dep_fill  = "#F2F2F2"
    color_label     = "#000000"
    color_caption   = "#333333"
    color_boundary  = "#444444"
    color_field     = "#222222"
    color_ion       = "#111111"

    # Strokes — match NCERT printed weight
    stroke_default          = "#000000"
    stroke_width_border     = 1.5
    stroke_width_wire       = 1.4
    stroke_width_field      = 1.1
    stroke_width_boundary   = 1.0

    # Carriers
    hole_radius          = 8.0
    electron_radius      = 7.0
    carrier_arrow_length = 18.0
    carrier_spacing_x    = 58.0
    carrier_spacing_y    = 46.0
    carrier_margin       = 30.0
    carrier_rows         = 3
    carrier_cols         = 3

    # Ions
    ion_rows      = 3
    ion_cols      = 1
    ion_spacing_y = 44.0

    # Field arrows
    field_arrow_head_size    = 6.0
    field_arrow_label_offset = 11.0
    field_e_y_fraction       = 0.35
    field_ei_y_fraction      = 0.65
    field_e_x_margin         = 14.0
    field_ei_x_margin        = 10.0

    # Semiconductor layout defaults
    semi_margin_x     = 85.0
    semi_margin_y     = 75.0
    semi_height       = 165.0
    semi_p_frac       = 0.40
    semi_dep_frac     = 0.14
    semi_n_frac       = 0.46
    circuit_gap       = 50.0
    circuit_arm_margin = 42.0
    switch_length     = 55.0
    battery_gap       = 18.0
    resistor_length   = 80.0

    label_top_offset      = -13.0
    label_bottom_offset   = 14.0
    title_y               = 30.0
    caption_bottom_margin = 18.0
    canvas_width          = 900.0
    canvas_height         = 480.0
