"""Ellipse primitive."""

from dataclasses import dataclass
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class Ellipse(SceneNode):
    rx: float = 0.0
    ry: float = 0.0

    def render(self, canvas) -> None:
        style_attrs = self.style.to_svgwrite_style()
        x, y = self.position
        elem = canvas.ellipse(center=(x, y), r=(self.rx, self.ry), **style_attrs)
        canvas.add(elem)

    def bounding_box(self) -> tuple[float, float, float, float]:
        x, y = self.position
        return (x - self.rx, y - self.ry, self.rx * 2, self.ry * 2)
