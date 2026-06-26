"""IonGrid — renders a grid of fixed-charge ion symbols for depletion regions."""

from dataclasses import dataclass
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class IonGrid(SceneNode):
    """
    Renders a rows×cols grid of fixed ion charge symbols.

    charge="positive" → "+" symbols  (donor ions in N-side of depletion region)
    charge="negative" → "−" symbols  (acceptor ions in P-side of depletion region)

    position is the centre of the top-left symbol in the grid.
    Reusable by any module that needs a periodic array of charge symbols.
    """

    rows: int = 3
    cols: int = 1
    spacing_x: float = 30.0
    spacing_y: float = 45.0
    charge: str = "positive"    # "positive" | "negative"
    symbol_size: float = 14.0

    def render(self, canvas) -> None:
        ox, oy = self.position
        symbol = "+" if self.charge == "positive" else "−"   # − (minus sign)
        fill = self.style.fill if self.style.fill not in ("none", "") else "#000000"
        fs = self.symbol_size

        for row in range(self.rows):
            for col in range(self.cols):
                cx = ox + col * self.spacing_x
                cy = oy + row * self.spacing_y
                canvas.add(canvas.text(
                    symbol,
                    insert=(cx, cy),
                    text_anchor="middle",
                    font_size=f"{fs}px",
                    font_family="Arial",
                    font_weight="bold",
                    fill=fill,
                ))

    def bounding_box(self) -> tuple[float, float, float, float]:
        ox, oy = self.position
        half = self.symbol_size / 2
        w = max(self.cols - 1, 0) * self.spacing_x + self.symbol_size
        h = max(self.rows - 1, 0) * self.spacing_y + self.symbol_size
        return (ox - half, oy - half, w, h)
