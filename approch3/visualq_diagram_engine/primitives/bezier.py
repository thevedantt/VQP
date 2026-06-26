"""Bezier / SVG path primitive."""

from dataclasses import dataclass
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class BezierPath(SceneNode):
    path_data: str = ""

    def render(self, canvas) -> None:
        style_attrs = self.style.to_svgwrite_style()
        elem = canvas.path(d=self.path_data, **style_attrs)
        canvas.add(elem)
