"""Grid layout — divides a canvas into rows and columns."""

from dataclasses import dataclass
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class GridCell:
    row: int
    col: int
    x: float
    y: float
    width: float
    height: float


class Grid:
    """Divides a rectangular area into a uniform row/column grid."""

    def __init__(
        self,
        rows: int,
        cols: int,
        x: float = 0,
        y: float = 0,
        width: float = 800,
        height: float = 600,
        padding: float = 0,
    ):
        self.rows = rows
        self.cols = cols
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.padding = padding

    @property
    def cell_width(self) -> float:
        return (self.width - self.padding * (self.cols + 1)) / self.cols

    @property
    def cell_height(self) -> float:
        return (self.height - self.padding * (self.rows + 1)) / self.rows

    def cell(self, row: int, col: int) -> GridCell:
        """Return the geometry for a specific grid cell (0-indexed)."""
        cx = self.x + self.padding + col * (self.cell_width + self.padding)
        cy = self.y + self.padding + row * (self.cell_height + self.padding)
        return GridCell(
            row=row, col=col, x=cx, y=cy,
            width=self.cell_width, height=self.cell_height,
        )

    def center_of(self, row: int, col: int) -> tuple[float, float]:
        """Return the center (x, y) of a grid cell."""
        c = self.cell(row, col)
        return (c.x + c.width / 2, c.y + c.height / 2)

    def place(self, node: SceneNode, row: int, col: int) -> None:
        """Set a node's position to the top-left of the specified cell."""
        c = self.cell(row, col)
        node.position = (c.x, c.y)

    def all_cells(self) -> list[GridCell]:
        return [self.cell(r, c) for r in range(self.rows) for c in range(self.cols)]
