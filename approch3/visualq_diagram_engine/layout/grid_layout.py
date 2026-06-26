"""GridLayout — arrange items in a rows×cols grid."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from visualq_diagram_engine.layout.base_layout import LayoutNode
from visualq_diagram_engine.layout.bounding_box import BoundingBox


@dataclass
class GridLayout(LayoutNode):
    """
    Place children into a uniform rows×cols grid.

    All cells are the same size (cell_w × cell_h).
    Useful for carrier grids, ion grids, and tabular symbol arrays.

    Usage::

        grid = GridLayout(node_id="hole_grid", rows=3, cols=3,
                          cell_w=58, cell_h=46)
        for hole in holes:
            grid.add(hole)
        positions = grid.apply(x=origin_x, y=origin_y)
    """
    children: list[LayoutNode] = field(default_factory=list)
    rows: int   = 1
    cols: int   = 1
    cell_w: float = 0.0
    cell_h: float = 0.0
    gap_x: float  = 0.0
    gap_y: float  = 0.0
    _placed_bb: Optional[BoundingBox] = field(default=None, repr=False, init=False)

    def add(self, child: LayoutNode) -> "GridLayout":
        self.children.append(child)
        return self

    def natural_size(self) -> tuple[float, float]:
        w = self.cols * self.cell_w + max(self.cols - 1, 0) * self.gap_x
        h = self.rows * self.cell_h + max(self.rows - 1, 0) * self.gap_y
        return (w, h)

    def apply(self, x: float, y: float) -> list[tuple[str, BoundingBox]]:
        result: list[tuple[str, BoundingBox]] = []
        for i, child in enumerate(self.children[: self.rows * self.cols]):
            row = i // self.cols
            col = i % self.cols
            cx = x + col * (self.cell_w + self.gap_x)
            cy = y + row * (self.cell_h + self.gap_y)
            result.extend(child.apply(cx, cy))

        w, h = self.natural_size()
        self._placed_bb = BoundingBox(x, y, w, h, self.node_id)
        return result

    def bounding_box(self) -> Optional[BoundingBox]:
        return self._placed_bb
