"""Style model for all scene primitives."""

from typing import Optional
from pydantic import BaseModel, Field


class Style(BaseModel):
    fill: str = "none"
    stroke: str = "#000000"
    stroke_width: float = 1.0
    opacity: float = 1.0
    font_size: float = 12.0
    font_family: str = "Arial"
    font_weight: str = "normal"
    text_anchor: str = "middle"
    dash_array: Optional[str] = None

    def to_svgwrite_style(self) -> dict:
        """Return svgwrite-compatible attribute dict."""
        attrs: dict = {
            "fill": self.fill,
            "stroke": self.stroke,
            "stroke_width": self.stroke_width,
            "opacity": self.opacity,
        }
        if self.dash_array:
            attrs["stroke_dasharray"] = self.dash_array
        return attrs

    def to_text_attrs(self) -> dict:
        """Return text-specific svgwrite attribute dict."""
        return {
            "fill": self.fill,
            "font_size": f"{self.font_size}px",
            "font_family": self.font_family,
            "font_weight": self.font_weight,
            "text_anchor": self.text_anchor,
            "opacity": self.opacity,
        }
