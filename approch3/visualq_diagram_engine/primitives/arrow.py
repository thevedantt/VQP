"""Arrow primitive — line with arrowhead(s) computed via vector math."""

import math
from dataclasses import dataclass, field
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class Arrow(SceneNode):
    start: tuple[float, float] = (0.0, 0.0)
    end: tuple[float, float] = (0.0, 0.0)
    head_size: float = 10.0
    bidirectional: bool = False

    def _arrowhead_points(
        self, tip: tuple[float, float], direction: tuple[float, float], size: float
    ) -> list[tuple[float, float]]:
        """Compute the three vertices of an arrowhead triangle."""
        dx, dy = direction
        length = math.hypot(dx, dy)
        if length == 0:
            return [tip, tip, tip]
        ux, uy = dx / length, dy / length
        # Perpendicular
        px, py = -uy, ux
        base_x = tip[0] - ux * size
        base_y = tip[1] - uy * size
        half = size * 0.4
        return [
            tip,
            (base_x + px * half, base_y + py * half),
            (base_x - px * half, base_y - py * half),
        ]

    def render(self, canvas) -> None:
        sx, sy = self.start
        ex, ey = self.end
        dx, dy = ex - sx, ey - sy

        color = self.style.stroke
        sw = self.style.stroke_width
        dash = self.style.dash_array

        line_attrs: dict = {
            "stroke": color,
            "stroke_width": sw,
            "fill": "none",
        }
        if dash:
            line_attrs["stroke_dasharray"] = dash

        # Shorten the line slightly so it doesn't overlap the arrowhead
        length = math.hypot(dx, dy)
        if length > 0:
            shrink = self.head_size * 0.8
            ratio = max(0.0, (length - shrink) / length)
            lx = sx + dx * ratio
            ly = sy + dy * ratio
        else:
            lx, ly = ex, ey

        elem = canvas.line(start=(sx, sy), end=(lx, ly), **line_attrs)
        canvas.add(elem)

        # Forward arrowhead at end
        pts = self._arrowhead_points((ex, ey), (dx, dy), self.head_size)
        head = canvas.polygon(points=pts, fill=color, stroke="none")
        canvas.add(head)

        if self.bidirectional:
            back_dir = (-dx, -dy)
            back_pts = self._arrowhead_points((sx, sy), back_dir, self.head_size)
            back_head = canvas.polygon(points=back_pts, fill=color, stroke="none")
            canvas.add(back_head)

    def bounding_box(self) -> tuple[float, float, float, float]:
        x1, y1 = self.start
        x2, y2 = self.end
        x = min(x1, x2)
        y = min(y1, y2)
        return (x, y, abs(x2 - x1), abs(y2 - y1))
