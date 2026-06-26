"""Rectangle primitive."""

from dataclasses import dataclass, field
from visualq_diagram_engine.core.scene import SceneNode
from visualq_diagram_engine.primitives.styles import Style


@dataclass
class Rectangle(SceneNode):
    width: float = 0.0
    height: float = 0.0
    corner_radius: float = 0.0

    def render(self, canvas) -> None:
        style_attrs = self.style.to_svgwrite_style()
        x, y = self.position
        elem = canvas.rect(
            insert=(x, y),
            size=(self.width, self.height),
            rx=self.corner_radius if self.corner_radius else None,
            ry=self.corner_radius if self.corner_radius else None,
            **style_attrs,
        )
        canvas.add(elem)

    def bounding_box(self) -> tuple[float, float, float, float]:
        x, y = self.position
        return (x, y, self.width, self.height)
