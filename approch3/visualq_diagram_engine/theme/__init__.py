"""theme — reusable styling system for scientific diagram engines."""

from visualq_diagram_engine.theme.base_theme import BaseTheme
from visualq_diagram_engine.theme.ncert_theme import NCERTTheme
from visualq_diagram_engine.theme.default_theme import DefaultTheme

__all__ = ["BaseTheme", "NCERTTheme", "DefaultTheme"]

# Active theme — can be overridden at runtime
active_theme: type[BaseTheme] = NCERTTheme


def set_theme(theme: type[BaseTheme]) -> None:
    """Set the global active theme used by all diagram modules."""
    global active_theme
    active_theme = theme


def get_theme() -> type[BaseTheme]:
    """Return the currently active theme class."""
    return active_theme
