"""
LayoutNode — abstract base class for all layout containers.

Every container:
  - Has an id and optional size hint
  - Can contain children (also LayoutNodes)
  - Exposes a bounding_box() after layout
  - Has an apply(x, y) method that computes children positions
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from visualq_diagram_engine.layout.bounding_box import BoundingBox


@dataclass
class LayoutNode(ABC):
    """Abstract base for all layout containers."""
    node_id: str = ""
    # Size hints — None means "compute from children"
    width_hint: Optional[float] = None
    height_hint: Optional[float] = None

    @abstractmethod
    def apply(self, x: float, y: float) -> list[tuple[str, BoundingBox]]:
        """
        Compute layout starting from (x, y).
        Returns list of (node_id, BoundingBox) for every placed node
        (self + all children, recursively).
        """
        ...

    @abstractmethod
    def natural_size(self) -> tuple[float, float]:
        """Return (width, height) based on content before layout is applied."""
        ...

    def bounding_box(self) -> Optional[BoundingBox]:
        """Return the bounding box after apply() has been called, or None."""
        return None


# ── Leaf ──────────────────────────────────────────────────────────────────────

@dataclass
class LeafNode(LayoutNode):
    """
    Wraps a fixed-size element (like a symbol or region box).
    The element already knows its width and height.
    """
    width: float  = 0.0
    height: float = 0.0
    _placed: Optional[BoundingBox] = field(default=None, repr=False, init=False)

    def apply(self, x: float, y: float) -> list[tuple[str, BoundingBox]]:
        bb = BoundingBox(x, y, self.width, self.height, self.node_id)
        self._placed = bb
        return [(self.node_id, bb)]

    def natural_size(self) -> tuple[float, float]:
        return (self.width, self.height)

    def bounding_box(self) -> Optional[BoundingBox]:
        return self._placed


# ── Spacer ────────────────────────────────────────────────────────────────────

@dataclass
class Spacer(LayoutNode):
    """Fixed empty gap consumed by HBox/VBox to add spacing."""
    size: float = 0.0

    def apply(self, x: float, y: float) -> list[tuple[str, BoundingBox]]:
        return []   # no node to place

    def natural_size(self) -> tuple[float, float]:
        return (self.size, self.size)
