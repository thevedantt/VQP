"""AutoLayout — applies grid placement + alignment + spacing in one pass."""

from visualq_diagram_engine.core.scene import SceneNode
from visualq_diagram_engine.layouts.grid import Grid
from visualq_diagram_engine.layouts.alignment import align_horizontal, align_vertical
from visualq_diagram_engine.layouts.spacing import distribute_evenly


class AutoLayout:
    """
    Convenience wrapper that applies a grid layout with optional alignment
    and even spacing passes over a list of scene nodes.

    Usage:
        layout = AutoLayout(rows=2, cols=3, x=50, y=100, width=700, height=400, padding=20)
        layout.apply(nodes)  # places nodes in grid order, left-to-right, top-to-bottom
    """

    def __init__(
        self,
        rows: int,
        cols: int,
        x: float = 0,
        y: float = 0,
        width: float = 800,
        height: float = 600,
        padding: float = 10,
    ):
        self.grid = Grid(rows=rows, cols=cols, x=x, y=y, width=width, height=height, padding=padding)

    def apply(self, nodes: list[SceneNode]) -> None:
        """Place nodes into grid cells in row-major order."""
        for i, node in enumerate(nodes):
            if i >= self.grid.rows * self.grid.cols:
                break
            row = i // self.grid.cols
            col = i % self.grid.cols
            self.grid.place(node, row, col)

    def apply_row(self, nodes: list[SceneNode], row: int, align_y: float | None = None) -> None:
        """Place nodes into a specific row, optionally aligning their y coordinates."""
        for col, node in enumerate(nodes):
            if col >= self.grid.cols:
                break
            self.grid.place(node, row, col)
        if align_y is not None:
            align_horizontal(nodes, align_y)

    def distribute_row(
        self, nodes: list[SceneNode], y: float, start_x: float, end_x: float
    ) -> None:
        """Place nodes at y, distributed evenly between start_x and end_x."""
        align_horizontal(nodes, y)
        distribute_evenly(nodes, axis="x", start=start_x, end=end_x)
