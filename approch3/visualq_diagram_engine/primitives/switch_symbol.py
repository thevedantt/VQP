"""SwitchSymbol — open/closed circuit switch (key) symbol."""

import math
from dataclasses import dataclass
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class SwitchSymbol(SceneNode):
    """
    Inline switch (key) symbol on a circuit wire.

    position = left contact.  Right contact is at x + length.

    open=False (default): closed switch, direct wire across the gap.
    open=True: tilted blade at 30° from horizontal (open circuit).

    Terminal dots are drawn at both contact ends. An optional label appears above.
    """

    length: float = 45.0
    open: bool = False
    orientation: str = "horizontal"
    label: str = "K"

    def render(self, canvas) -> None:
        x, y = self.position
        sw = self.style.stroke_width
        stroke = self.style.stroke
        if self.orientation == "horizontal":
            self._render_h(canvas, x, y, sw, stroke)

    def _render_h(self, canvas, x: float, y: float, sw: float, stroke: str) -> None:
        stub      = self.length * 0.28
        left_t    = x + stub
        right_t   = x + self.length - stub

        # Left stub
        canvas.add(canvas.line(
            start=(x, y), end=(left_t, y),
            stroke=stroke, stroke_width=sw, fill="none",
        ))

        # Terminal dots
        canvas.add(canvas.circle(center=(left_t,  y), r=2.5, fill=stroke, stroke="none"))
        canvas.add(canvas.circle(center=(right_t, y), r=2.5, fill=stroke, stroke="none"))

        gap = right_t - left_t
        if self.open:
            # Tilted blade at 30° upward from left terminal
            blade = gap * 0.85
            angle = math.radians(30)
            canvas.add(canvas.line(
                start=(left_t, y),
                end=(left_t + math.cos(angle) * blade, y - math.sin(angle) * blade),
                stroke=stroke, stroke_width=sw, fill="none",
            ))
        else:
            canvas.add(canvas.line(
                start=(left_t, y), end=(right_t, y),
                stroke=stroke, stroke_width=sw, fill="none",
            ))

        # Right stub
        canvas.add(canvas.line(
            start=(right_t, y), end=(x + self.length, y),
            stroke=stroke, stroke_width=sw, fill="none",
        ))

        # Label above centre
        if self.label:
            canvas.add(canvas.text(
                self.label,
                insert=((left_t + right_t) / 2, y - 12),
                text_anchor="middle",
                font_size="11px", font_family="Arial",
                fill=stroke,
            ))

    def bounding_box(self) -> tuple[float, float, float, float]:
        x, y = self.position
        return (x, y - 20, self.length, 30)

    def ports(self) -> dict[str, tuple[float, float]]:
        x, y = self.position
        return {
            "left":  (x, y),
            "right": (x + self.length, y),
            "entry": (x, y),
            "exit":  (x + self.length, y),
        }
