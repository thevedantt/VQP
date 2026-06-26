"""WirePath — a multi-segment orthogonal wire for circuit diagrams."""

from dataclasses import dataclass, field
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class WirePath(SceneNode):
    """
    Renders consecutive line segments between a list of ordered waypoints.

    Intended for circuit wiring: all segments should be axis-aligned
    (horizontal or vertical), but no constraint is enforced.

    position is unused; geometry is fully determined by waypoints.
    Replaces multiple individual Line objects with a single spec entry,
    making the YAML template concise and the intent readable.
    """

    waypoints: list[tuple[float, float]] = field(default_factory=list)

    def render(self, canvas) -> None:
        if len(self.waypoints) < 2:
            return
        stroke = self.style.stroke
        sw = self.style.stroke_width
        dash_attrs: dict = {}
        if self.style.dash_array:
            dash_attrs["stroke_dasharray"] = self.style.dash_array

        for i in range(len(self.waypoints) - 1):
            x1, y1 = self.waypoints[i]
            x2, y2 = self.waypoints[i + 1]
            canvas.add(canvas.line(
                start=(x1, y1), end=(x2, y2),
                stroke=stroke, stroke_width=sw, fill="none",
                **dash_attrs,
            ))

    def bounding_box(self) -> tuple[float, float, float, float]:
        if not self.waypoints:
            return (0.0, 0.0, 0.0, 0.0)
        xs = [p[0] for p in self.waypoints]
        ys = [p[1] for p in self.waypoints]
        x, y = min(xs), min(ys)
        return (x, y, max(xs) - x, max(ys) - y)
