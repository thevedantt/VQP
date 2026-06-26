"""SVG canvas wrapper around svgwrite.Drawing."""

import logging
import svgwrite
from svgwrite.container import Defs

logger = logging.getLogger(__name__)


class SVGCanvas:
    def __init__(self, width: float, height: float, background: str = "#FFFFFF"):
        self._drawing = svgwrite.Drawing(
            size=(f"{width}px", f"{height}px"),
            profile="full",
        )
        self._drawing.viewbox(0, 0, width, height)
        # Background rect
        self._drawing.add(
            self._drawing.rect(
                insert=(0, 0),
                size=(width, height),
                fill=background,
            )
        )

    def add(self, element) -> None:
        self._drawing.add(element)

    def add_defs(self, element) -> None:
        self._drawing.defs.add(element)

    def define_arrowhead_marker(self, marker_id: str, color: str, size: float = 8) -> None:
        """Define an SVG <marker> element for arrowheads."""
        marker = self._drawing.marker(
            id=marker_id,
            insert=(size, size / 2),
            size=(size, size),
            orient="auto",
        )
        marker.add(
            self._drawing.polygon(
                points=[(0, 0), (size, size / 2), (0, size)],
                fill=color,
            )
        )
        self.add_defs(marker)

    def get_drawing(self) -> svgwrite.Drawing:
        return self._drawing

    def save(self, path: str) -> None:
        self._drawing.saveas(path)
        logger.debug("SVG saved to %s", path)

    # Convenience factory methods so primitives can create svgwrite shapes
    def rect(self, **kwargs):
        return self._drawing.rect(**kwargs)

    def circle(self, **kwargs):
        return self._drawing.circle(**kwargs)

    def ellipse(self, **kwargs):
        return self._drawing.ellipse(**kwargs)

    def line(self, **kwargs):
        return self._drawing.line(**kwargs)

    def polygon(self, **kwargs):
        return self._drawing.polygon(**kwargs)

    def path(self, **kwargs):
        return self._drawing.path(**kwargs)

    def text(self, *args, **kwargs):
        return self._drawing.text(*args, **kwargs)
