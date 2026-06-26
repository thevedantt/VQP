"""HBox — horizontal layout container."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from visualq_diagram_engine.layout.base_layout import LayoutNode, Spacer
from visualq_diagram_engine.layout.bounding_box import BoundingBox
from visualq_diagram_engine.layout.alignment import VAlign, align_y


@dataclass
class HBox(LayoutNode):
    """
    Arrange children left-to-right with an optional gap.

    Children can be any LayoutNode (LeafNode, VBox, another HBox, etc.)
    `valign` controls how children are aligned vertically when they have
    different heights.

    Usage::

        box = HBox(node_id="circuit_row", gap=18)
        box.add(switch_node)
        box.add(battery_node)
        box.add(resistor_node)
        positions = box.apply(x=43, y=290)
    """

    children: list[LayoutNode] = field(default_factory=list)
    gap: float = 0.0
    valign: VAlign = VAlign.CENTER
    _placed_bb: Optional[BoundingBox] = field(default=None, repr=False, init=False)

    def add(self, child: LayoutNode) -> "HBox":
        self.children.append(child)
        return self

    def natural_size(self) -> tuple[float, float]:
        if not self.children:
            return (0.0, 0.0)
        total_w = sum(c.natural_size()[0] for c in self.children)
        n_gaps  = sum(1 for c in self.children if not isinstance(c, Spacer))
        total_w += self.gap * max(n_gaps - 1, 0)
        max_h = max((c.natural_size()[1] for c in self.children), default=0.0)
        return (total_w, max_h)

    def apply(self, x: float, y: float) -> list[tuple[str, BoundingBox]]:
        _, max_h = self.natural_size()
        cx = x
        result: list[tuple[str, BoundingBox]] = []

        for i, child in enumerate(self.children):
            cw, ch = child.natural_size()
            cy = align_y(ch, y, max_h, self.valign)
            result.extend(child.apply(cx, cy))
            cx += cw
            if i < len(self.children) - 1 and not isinstance(child, Spacer):
                cx += self.gap

        total_w, total_h = cx - x, max_h
        self._placed_bb = BoundingBox(x, y, total_w, total_h, self.node_id)
        return result

    def bounding_box(self) -> Optional[BoundingBox]:
        return self._placed_bb
