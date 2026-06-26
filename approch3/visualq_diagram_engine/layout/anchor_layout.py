"""
AnchorLayout — position a node relative to an anchor point on another node.

Supports CSS-like attachment: "place this node's top-left at target's bottom-center".
Combined with the constraint solver, this eliminates almost all manual coordinates.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from visualq_diagram_engine.layout.base_layout import LayoutNode
from visualq_diagram_engine.layout.bounding_box import BoundingBox


@dataclass
class AnchorLayout(LayoutNode):
    """
    Attach node relative to a target bounding box.

    Parameters
    ----------
    target_bb   : BoundingBox of the element to attach to
    target_anchor : anchor name on the target ("bc" = bottom-center, etc.)
    self_anchor   : which anchor of THIS node aligns to target_anchor
    offset_x, offset_y : additional pixel offsets after anchoring

    Example — place a caption centred 20 px below a figure::

        AnchorLayout(
            node_id="caption",
            width=500, height=20,
            target_bb=figure.bounding_box(),
            target_anchor="bc",
            self_anchor="tc",
            offset_y=10,
        )
    """
    width: float  = 0.0
    height: float = 0.0
    target_bb: Optional[BoundingBox] = None
    target_anchor: str = "bc"    # anchor on the target
    self_anchor:   str = "tc"    # anchor on self that snaps to target_anchor
    offset_x: float = 0.0
    offset_y: float = 0.0
    _placed_bb: Optional[BoundingBox] = field(default=None, repr=False, init=False)

    def natural_size(self) -> tuple[float, float]:
        return (self.width, self.height)

    def apply(self, x: float = 0, y: float = 0) -> list[tuple[str, BoundingBox]]:
        if self.target_bb is None:
            bb = BoundingBox(x, y, self.width, self.height, self.node_id)
        else:
            # Get target anchor coordinates
            tx, ty = self.target_bb.anchor(self.target_anchor)
            # Build a temp bb at (0,0) to get the self-anchor offset
            tmp = BoundingBox(0, 0, self.width, self.height)
            ax, ay = tmp.anchor(self.self_anchor)
            # Position this node so self_anchor aligns to target_anchor
            bx = tx - ax + self.offset_x
            by = ty - ay + self.offset_y
            bb = BoundingBox(bx, by, self.width, self.height, self.node_id)

        self._placed_bb = bb
        return [(self.node_id, bb)]

    def bounding_box(self) -> Optional[BoundingBox]:
        return self._placed_bb
