"""Padding and Margin — inset / outset a layout node."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from visualq_diagram_engine.layout.base_layout import LayoutNode
from visualq_diagram_engine.layout.bounding_box import BoundingBox


@dataclass
class Padding(LayoutNode):
    """
    Wraps a single child with uniform padding on all sides.

    The outer bounding box is child_size + 2*pad in each axis.
    The child is placed at (x+pad, y+pad).
    """
    child: Optional[LayoutNode] = None
    pad_left:   float = 0.0
    pad_right:  float = 0.0
    pad_top:    float = 0.0
    pad_bottom: float = 0.0
    _placed_bb: Optional[BoundingBox] = field(default=None, repr=False, init=False)

    @classmethod
    def uniform(cls, child: LayoutNode, pad: float, node_id: str = "") -> "Padding":
        return cls(node_id=node_id, child=child,
                   pad_left=pad, pad_right=pad, pad_top=pad, pad_bottom=pad)

    @classmethod
    def symmetric(cls, child: LayoutNode,
                  horizontal: float = 0, vertical: float = 0,
                  node_id: str = "") -> "Padding":
        return cls(node_id=node_id, child=child,
                   pad_left=horizontal, pad_right=horizontal,
                   pad_top=vertical, pad_bottom=vertical)

    def natural_size(self) -> tuple[float, float]:
        if self.child is None:
            return (self.pad_left + self.pad_right, self.pad_top + self.pad_bottom)
        cw, ch = self.child.natural_size()
        return (cw + self.pad_left + self.pad_right,
                ch + self.pad_top  + self.pad_bottom)

    def apply(self, x: float, y: float) -> list[tuple[str, BoundingBox]]:
        result: list[tuple[str, BoundingBox]] = []
        if self.child is not None:
            result.extend(self.child.apply(x + self.pad_left, y + self.pad_top))
        w, h = self.natural_size()
        self._placed_bb = BoundingBox(x, y, w, h, self.node_id)
        return result

    def bounding_box(self) -> Optional[BoundingBox]:
        return self._placed_bb


@dataclass
class Margin(Padding):
    """
    Alias for Padding used when describing outer spacing around a node.
    Semantically, padding is inner space; margin is outer space.
    Both produce identical layout results.
    """
    pass
