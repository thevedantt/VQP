"""BatterySymbol — IEC-style battery inline on a circuit wire."""

from dataclasses import dataclass
from visualq_diagram_engine.core.scene import SceneNode

# Total width of a single-cell horizontal battery (entry x to exit x)
BATTERY_CELL_WIDTH: int = 40


@dataclass
class BatterySymbol(SceneNode):
    """
    Renders a battery symbol inline on a circuit wire.

    position = the LEFT contact point (horizontal) or TOP contact (vertical).

    For a single-cell horizontal battery:
      - long bar (positive) is at x+10
      - short bar (negative) is at x+25
      - right exit is at x+40

    Renders wire stubs, the bar pair, and +/- labels.
    """

    orientation: str = "horizontal"
    positive_on: str = "left"    # "left" → long bar is on the entry side
    cells: int = 1

    def render(self, canvas) -> None:
        x, y = self.position
        sw = self.style.stroke_width
        stroke = self.style.stroke
        if self.orientation == "horizontal":
            self._render_h(canvas, x, y, sw, stroke)
        else:
            self._render_v(canvas, x, y, sw, stroke)

    def _render_h(self, canvas, x: float, y: float, sw: float, stroke: str) -> None:
        cw = BATTERY_CELL_WIDTH   # 40 px per cell
        long_half  = 14           # ½ height of the positive (long) bar
        short_half =  8           # ½ height of the negative (short) bar
        bar_gap    = 15           # distance between bar centres

        for cell in range(self.cells):
            ox = x + cell * cw

            if self.positive_on == "left":
                long_x  = ox + 10
                short_x = ox + 10 + bar_gap
            else:
                short_x = ox + 10
                long_x  = ox + 10 + bar_gap

            first_bar = long_x if self.positive_on == "left" else short_x
            last_bar  = short_x if self.positive_on == "left" else long_x

            # Left stub: entry → first bar
            canvas.add(canvas.line(
                start=(ox, y), end=(first_bar, y),
                stroke=stroke, stroke_width=sw, fill="none",
            ))
            # Long bar (positive, thicker)
            canvas.add(canvas.line(
                start=(long_x, y - long_half), end=(long_x, y + long_half),
                stroke=stroke, stroke_width=sw * 2.5, fill="none",
            ))
            # Short bar (negative, thinner)
            canvas.add(canvas.line(
                start=(short_x, y - short_half), end=(short_x, y + short_half),
                stroke=stroke, stroke_width=sw * 1.5, fill="none",
            ))
            # Right stub: last bar → exit
            canvas.add(canvas.line(
                start=(last_bar, y), end=(ox + cw, y),
                stroke=stroke, stroke_width=sw, fill="none",
            ))

            # Labels above bars
            canvas.add(canvas.text(
                "+",
                insert=(long_x, y - long_half - 5),
                text_anchor="middle",
                font_size="13px", font_family="Arial", font_weight="bold",
                fill=stroke,
            ))
            canvas.add(canvas.text(
                "−",     # Unicode minus sign
                insert=(short_x, y - short_half - 5),
                text_anchor="middle",
                font_size="13px", font_family="Arial", font_weight="bold",
                fill=stroke,
            ))

    def _render_v(self, canvas, x: float, y: float, sw: float, stroke: str) -> None:
        """Vertical wire battery: bars are horizontal."""
        long_half  = 14
        short_half =  8
        bar_gap    = 12
        cell_h     = bar_gap + 16

        for cell in range(self.cells):
            oy = y + cell * cell_h
            long_y  = oy + 8
            short_y = oy + 8 + bar_gap

            canvas.add(canvas.line(
                start=(x, oy), end=(x, long_y),
                stroke=stroke, stroke_width=sw, fill="none",
            ))
            canvas.add(canvas.line(
                start=(x - long_half, long_y), end=(x + long_half, long_y),
                stroke=stroke, stroke_width=sw * 2.5, fill="none",
            ))
            canvas.add(canvas.line(
                start=(x - short_half, short_y), end=(x + short_half, short_y),
                stroke=stroke, stroke_width=sw * 1.5, fill="none",
            ))
            canvas.add(canvas.line(
                start=(x, short_y), end=(x, oy + cell_h),
                stroke=stroke, stroke_width=sw, fill="none",
            ))

    def bounding_box(self) -> tuple[float, float, float, float]:
        x, y = self.position
        if self.orientation == "horizontal":
            return (x, y - 20, self.cells * BATTERY_CELL_WIDTH, 40)
        return (x - 20, y, 40, self.cells * 28 + 16)

    def ports(self) -> dict[str, tuple[float, float]]:
        x, y = self.position
        if self.orientation == "horizontal":
            total_w = self.cells * BATTERY_CELL_WIDTH
            if self.positive_on == "left":
                return {"positive": (x, y), "negative": (x + total_w, y),
                        "left": (x, y), "right": (x + total_w, y)}
            return {"positive": (x + total_w, y), "negative": (x, y),
                    "left": (x, y), "right": (x + total_w, y)}
        # vertical
        total_h = self.cells * 28 + 16
        return {"top": (x, y), "bottom": (x, y + total_h),
                "positive": (x, y), "negative": (x, y + total_h)}
