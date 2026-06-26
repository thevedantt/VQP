"""VBox — vertical layout container."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from visualq_diagram_engine.layout.base_layout import LayoutNode, Spacer
from visualq_diagram_engine.layout.bounding_box import BoundingBox
from visualq_diagram_engine.layout.alignment import HAlign, align_x


@dataclass
class VBox(LayoutNode):
    """
    Arrange children top-to-bottom with an optional gap.

    Usage::

        vbox = VBox(node_id="diagram_column", gap=50)
        vbox.add(semiconductor_node)
        vbox.add(circuit_node)
        vbox.add(caption_node)
        positions = vbox.apply(x=canvas_x, y=top_y)
    """

    children: list[LayoutNode] = field(default_factory=list)
    gap: float = 0.0
    halign: HAlign = HAlign.CENTER
    _placed_bb: Optional[BoundingBox] = field(default=None, repr=False, init=False)

    def add(self, child: LayoutNode) -> "VBox":
        self.children.append(child)
        return self

    def natural_size(self) -> tuple[float, float]:
        if not self.children:
            return (0.0, 0.0)
        total_h = sum(c.natural_size()[1] for c in self.children)
        n_gaps  = sum(1 for c in self.children if not isinstance(c, Spacer))
        total_h += self.gap * max(n_gaps - 1, 0)
        max_w   = max((c.natural_size()[0] for c in self.children), default=0.0)
        return (max_w, total_h)

    def apply(self, x: float, y: float) -> list[tuple[str, BoundingBox]]:
        max_w, _ = self.natural_size()
        cy = y
        result: list[tuple[str, BoundingBox]] = []

        for i, child in enumerate(self.children):
            cw, ch = child.natural_size()
            cx = align_x(cw, x, max_w, self.halign)
            result.extend(child.apply(cx, cy))
            cy += ch
            if i < len(self.children) - 1 and not isinstance(child, Spacer):
                cy += self.gap

        total_w, total_h = max_w, cy - y
        self._placed_bb = BoundingBox(x, y, total_w, total_h, self.node_id)
        return result

    def bounding_box(self) -> Optional[BoundingBox]:
        return self._placed_bb
