"""
Typography — named text styles for consistent typography across all diagram types.

Import Typography and use its class attributes instead of scattering font sizes
through individual module code or YAML templates.

Usage::

    from visualq_diagram_engine.typography import Typography
    style = Typography.REGION_LABEL        # returns a Style instance
    style = Typography.for_role("title")   # dynamic lookup
"""

from visualq_diagram_engine.primitives.styles import Style


class Typography:
    """Predefined text styles for the VisualQ scientific diagram engine."""

    # ── Document-level ──────────────────────────────────────────────────────
    TITLE: Style = Style(
        fill="#000000", stroke="none",
        font_size=17.0, font_weight="bold",
        font_family="Arial", text_anchor="middle",
    )
    CAPTION: Style = Style(
        fill="#222222", stroke="none",
        font_size=11.0, font_family="Arial",
        text_anchor="middle",
    )
    FIGURE_NUMBER: Style = Style(
        fill="#222222", stroke="none",
        font_size=11.0, font_family="Arial",
        text_anchor="middle",
    )

    # ── Region / component labels ────────────────────────────────────────────
    REGION_LABEL: Style = Style(
        fill="#000000", stroke="none",
        font_size=18.0, font_weight="bold",
        font_family="Arial", text_anchor="middle",
    )
    COMPONENT_LABEL: Style = Style(
        fill="#000000", stroke="none",
        font_size=11.0, font_family="Arial",
        text_anchor="middle",
    )
    SMALL_LABEL: Style = Style(
        fill="#333333", stroke="none",
        font_size=9.0, font_family="Arial",
        text_anchor="middle",
    )

    # ── Physics-specific ────────────────────────────────────────────────────
    ION_SYMBOL: Style = Style(
        fill="#000000", stroke="none",
        font_size=15.0, font_weight="bold",
        font_family="Arial", text_anchor="middle",
    )
    FIELD_LABEL: Style = Style(
        fill="#000000", stroke="none",
        font_size=10.0, font_family="Arial",
        text_anchor="middle",
    )
    CARRIER_LABEL: Style = Style(
        fill="#000000", stroke="none",
        font_size=11.0, font_family="Arial",
        text_anchor="middle",
    )

    # ── Lookup ──────────────────────────────────────────────────────────────
    _ROLES: dict[str, str] = {
        "title": "TITLE",
        "caption": "CAPTION",
        "figure_number": "FIGURE_NUMBER",
        "region_label": "REGION_LABEL",
        "component_label": "COMPONENT_LABEL",
        "small_label": "SMALL_LABEL",
        "ion_symbol": "ION_SYMBOL",
        "field_label": "FIELD_LABEL",
        "carrier_label": "CARRIER_LABEL",
    }

    @classmethod
    def for_role(cls, role: str) -> Style:
        """Return the Style for a named typography role. Raises KeyError if unknown."""
        attr = cls._ROLES.get(role.lower())
        if attr is None:
            raise KeyError(f"Unknown typography role: '{role}'. "
                           f"Valid roles: {list(cls._ROLES)}")
        return getattr(cls, attr)
