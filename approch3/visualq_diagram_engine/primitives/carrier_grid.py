"""CarrierGrid — composite primitive rendering a grid of charge carriers in NCERT style."""

import math
from dataclasses import dataclass
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class CarrierGrid(SceneNode):
    """
    Renders a rows×cols grid of charge carriers.

    Holes    (carrier_type="hole"):     hollow circles, white fill, black outline.
    Electrons(carrier_type="electron"): filled solid black circles.

    Per NCERT convention, holes are represented as plain hollow circles — no "+"
    symbol inside.  Use an IonGrid for explicit charge symbols.

    Optionally draws a short directional arrow from each carrier's edge to
    indicate majority-carrier drift direction.

    position is the CENTER of the top-left carrier in the grid.
    """

    rows: int = 3
    cols: int = 3
    spacing_x: float = 55.0
    spacing_y: float = 50.0
    carrier_type: str = "hole"       # "hole" | "electron"
    carrier_radius: float = 8.0
    show_arrows: bool = False
    arrow_direction: str = "right"   # "right" | "left" | "up" | "down"
    arrow_length: float = 20.0

    def _dir(self) -> tuple[float, float]:
        return {
            "right": (1.0, 0.0),
            "left":  (-1.0, 0.0),
            "up":    (0.0, -1.0),
            "down":  (0.0, 1.0),
        }.get(self.arrow_direction, (1.0, 0.0))

    def render(self, canvas) -> None:
        ox, oy = self.position
        r = self.carrier_radius
        sw = self.style.stroke_width
        stroke = self.style.stroke
        is_hole = self.carrier_type.lower() == "hole"
        fill = "#FFFFFF" if is_hole else "#000000"
        dx, dy = self._dir()

        for row in range(self.rows):
            for col in range(self.cols):
                cx = ox + col * self.spacing_x
                cy = oy + row * self.spacing_y

                # Carrier circle
                canvas.add(canvas.circle(
                    center=(cx, cy), r=r,
                    fill=fill, stroke=stroke, stroke_width=sw,
                ))

                # Movement arrow from the carrier's edge
                if self.show_arrows:
                    gap = r + 2
                    ax, ay = cx + dx * gap, cy + dy * gap
                    head_size = 5.0
                    # Shorten line so it doesn't overlap the arrowhead
                    line_ex = ax + dx * max(0.0, self.arrow_length - head_size * 0.85)
                    line_ey = ay + dy * max(0.0, self.arrow_length - head_size * 0.85)
                    tip_x = ax + dx * self.arrow_length
                    tip_y = ay + dy * self.arrow_length

                    canvas.add(canvas.line(
                        start=(ax, ay), end=(line_ex, line_ey),
                        stroke=stroke, stroke_width=max(sw * 0.75, 0.8), fill="none",
                    ))

                    # Arrowhead triangle
                    seg_len = math.hypot(tip_x - ax, tip_y - ay)
                    if seg_len > 0:
                        ux = (tip_x - ax) / seg_len
                        uy = (tip_y - ay) / seg_len
                        px, py = -uy, ux
                        bx = tip_x - ux * head_size
                        by = tip_y - uy * head_size
                        half = head_size * 0.42
                        pts = [
                            (tip_x, tip_y),
                            (bx + px * half, by + py * half),
                            (bx - px * half, by - py * half),
                        ]
                        canvas.add(canvas.polygon(points=pts, fill=stroke, stroke="none"))

    def bounding_box(self) -> tuple[float, float, float, float]:
        ox, oy = self.position
        r = self.carrier_radius
        w = (self.cols - 1) * self.spacing_x + r * 2
        h = (self.rows - 1) * self.spacing_y + r * 2
        return (ox - r, oy - r, w, h)
