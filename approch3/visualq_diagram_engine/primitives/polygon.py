"""Polygon primitive."""

from dataclasses import dataclass, field
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class Polygon(SceneNode):
    points: list[tuple[float, float]] = field(default_factory=list)

    def render(self, canvas) -> None:
        style_attrs = self.style.to_svgwrite_style()
        elem = canvas.polygon(points=self.points, **style_attrs)
        canvas.add(elem)

    def bounding_box(self) -> tuple[float, float, float, float]:
        if not self.points:
            return (0.0, 0.0, 0.0, 0.0)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
