"""Circle primitive."""

from dataclasses import dataclass
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class Circle(SceneNode):
    radius: float = 0.0

    def render(self, canvas) -> None:
        style_attrs = self.style.to_svgwrite_style()
        x, y = self.position
        elem = canvas.circle(center=(x, y), r=self.radius, **style_attrs)
        canvas.add(elem)

    def bounding_box(self) -> tuple[float, float, float, float]:
        x, y = self.position
        return (x - self.radius, y - self.radius, self.radius * 2, self.radius * 2)
