"""Line primitive."""

from dataclasses import dataclass, field
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class Line(SceneNode):
    start: tuple[float, float] = (0.0, 0.0)
    end: tuple[float, float] = (0.0, 0.0)

    def render(self, canvas) -> None:
        style_attrs = self.style.to_svgwrite_style()
        # Lines have no fill
        style_attrs["fill"] = "none"
        elem = canvas.line(start=self.start, end=self.end, **style_attrs)
        canvas.add(elem)

    def bounding_box(self) -> tuple[float, float, float, float]:
        x1, y1 = self.start
        x2, y2 = self.end
        x = min(x1, x2)
        y = min(y1, y2)
        return (x, y, abs(x2 - x1), abs(y2 - y1))
