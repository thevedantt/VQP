"""FieldArrow — a named, labelled directional arrow for electric/magnetic fields."""

import math
from dataclasses import dataclass, field
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class FieldArrow(SceneNode):
    """
    Renders a single directional arrow with an optional text label.

    position = tail (start) of the arrow.
    end      = tip  of the arrow.

    The label is placed above or below the arrow's midpoint.
    Reusable for internal field (Ei), external applied field (E), magnetic field
    lines, force vectors, or any annotated vector quantity.
    """

    end: tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    head_size: float = 7.0
    label: str = ""
    label_side: str = "above"    # "above" | "below"
    label_offset: float = 12.0

    def _arrowhead(
        self,
        tip: tuple[float, float],
        dx: float, dy: float,
        size: float,
    ) -> list[tuple[float, float]]:
        length = math.hypot(dx, dy)
        if length == 0:
            return [tip, tip, tip]
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        bx = tip[0] - ux * size
        by = tip[1] - uy * size
        half = size * 0.42
        return [
            tip,
            (bx + px * half, by + py * half),
            (bx - px * half, by - py * half),
        ]

    def render(self, canvas) -> None:
        sx, sy = self.position
        ex, ey = self.end
        dx, dy = ex - sx, ey - sy
        stroke = self.style.stroke
        sw = self.style.stroke_width

        # Shorten line body to avoid overlap with arrowhead
        length = math.hypot(dx, dy)
        shrink = self.head_size * 0.8
        if length > shrink:
            ratio = (length - shrink) / length
            lx = sx + dx * ratio
            ly = sy + dy * ratio
        else:
            lx, ly = ex, ey

        line_attrs: dict = {"stroke": stroke, "stroke_width": sw, "fill": "none"}
        if self.style.dash_array:
            line_attrs["stroke_dasharray"] = self.style.dash_array
        canvas.add(canvas.line(start=(sx, sy), end=(lx, ly), **line_attrs))

        pts = self._arrowhead((ex, ey), dx, dy, self.head_size)
        canvas.add(canvas.polygon(points=pts, fill=stroke, stroke="none"))

        if self.label:
            mx = (sx + ex) / 2
            my = (sy + ey) / 2
            sign = -1 if self.label_side == "above" else 1
            label_y = my + sign * self.label_offset
            text_fill = self.style.fill if self.style.fill not in ("none", "") else stroke
            canvas.add(canvas.text(
                self.label,
                insert=(mx, label_y),
                text_anchor="middle",
                font_size=f"{self.style.font_size}px",
                font_family=self.style.font_family,
                fill=text_fill,
            ))

    def bounding_box(self) -> tuple[float, float, float, float]:
        sx, sy = self.position
        ex, ey = self.end
        x, y = min(sx, ex), min(sy, ey)
        return (x, y, abs(ex - sx), abs(ey - sy))
