"""ResistorSymbol — rectangular box resistor (Indian/European textbook style)."""

from dataclasses import dataclass
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class ResistorSymbol(SceneNode):
    """
    Rectangular resistor symbol inline on a circuit wire.

    position = left contact (horizontal) or top contact (vertical).
    Right contact is at x + length.

    Draws wire stubs on both sides of a centred rectangle, plus an optional
    label above the box.
    """

    length: float = 70.0
    body_height: float = 14.0
    orientation: str = "horizontal"
    label: str = "R"

    def render(self, canvas) -> None:
        x, y = self.position
        sw = self.style.stroke_width
        stroke = self.style.stroke

        if self.orientation == "horizontal":
            stub   = self.length * 0.18
            box_x  = x + stub
            box_w  = self.length - 2 * stub
            half_h = self.body_height / 2

            # Left stub
            canvas.add(canvas.line(
                start=(x, y), end=(box_x, y),
                stroke=stroke, stroke_width=sw, fill="none",
            ))
            # Rectangle
            canvas.add(canvas.rect(
                insert=(box_x, y - half_h),
                size=(box_w, self.body_height),
                fill="#FFFFFF", stroke=stroke, stroke_width=sw,
            ))
            # Right stub
            canvas.add(canvas.line(
                start=(box_x + box_w, y), end=(x + self.length, y),
                stroke=stroke, stroke_width=sw, fill="none",
            ))
            # Label above centre of box
            if self.label:
                canvas.add(canvas.text(
                    self.label,
                    insert=(box_x + box_w / 2, y - half_h - 4),
                    text_anchor="middle",
                    font_size="11px", font_family="Arial",
                    fill=stroke,
                ))

    def bounding_box(self) -> tuple[float, float, float, float]:
        x, y = self.position
        return (x, y - self.body_height / 2, self.length, self.body_height)

    def ports(self) -> dict[str, tuple[float, float]]:
        x, y = self.position
        return {
            "left":  (x, y),
            "right": (x + self.length, y),
            "entry": (x, y),
            "exit":  (x + self.length, y),
        }
