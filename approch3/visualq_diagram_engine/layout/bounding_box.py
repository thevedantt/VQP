"""
BoundingBox — unified geometry object that every SceneNode can return.

Provides anchor points, containment checks, padding, and union operations
so that layout containers and constraint solvers can work purely with
geometry without touching the scene graph.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class BoundingBox:
    """
    Axis-aligned bounding box with named anchor points.

    All coordinates are in SVG canvas space (y increases downward).
    Anchor names follow CSS logical properties:
        tl/tc/tr  — top row
        ml/mc/mr  — middle row
        bl/bc/br  — bottom row
    """
    x: float
    y: float
    width: float
    height: float
    node_id: str = ""

    # ── Edges ────────────────────────────────────────────────────────────────

    @property
    def left(self)   -> float: return self.x
    @property
    def right(self)  -> float: return self.x + self.width
    @property
    def top(self)    -> float: return self.y
    @property
    def bottom(self) -> float: return self.y + self.height
    @property
    def cx(self)     -> float: return self.x + self.width  / 2
    @property
    def cy(self)     -> float: return self.y + self.height / 2

    def center(self) -> tuple[float, float]:
        return (self.cx, self.cy)

    # ── Named anchors ─────────────────────────────────────────────────────────

    ANCHOR_NAMES = ("tl", "tc", "tr", "ml", "mc", "mr", "bl", "bc", "br")

    def anchor(self, name: str) -> tuple[float, float]:
        """Return the (x, y) coordinate of a named anchor point."""
        table: dict[str, tuple[float, float]] = {
            "tl": (self.left,  self.top),
            "tc": (self.cx,    self.top),
            "tr": (self.right, self.top),
            "ml": (self.left,  self.cy),
            "mc": (self.cx,    self.cy),
            "mr": (self.right, self.cy),
            "bl": (self.left,  self.bottom),
            "bc": (self.cx,    self.bottom),
            "br": (self.right, self.bottom),
        }
        if name not in table:
            raise KeyError(f"Unknown anchor '{name}'. Valid: {self.ANCHOR_NAMES}")
        return table[name]

    def anchor_points(self) -> dict[str, tuple[float, float]]:
        """Return all nine named anchor points."""
        return {name: self.anchor(name) for name in self.ANCHOR_NAMES}

    # ── Spatial relations ─────────────────────────────────────────────────────

    def contains(self, other: "BoundingBox", tolerance: float = 0) -> bool:
        return (self.left   <= other.left   + tolerance and
                self.right  >= other.right  - tolerance and
                self.top    <= other.top    + tolerance and
                self.bottom >= other.bottom - tolerance)

    def overlaps(self, other: "BoundingBox", tolerance: float = 2.0) -> bool:
        return (self.left  < other.right  - tolerance and
                self.right > other.left   + tolerance and
                self.top   < other.bottom - tolerance and
                self.bottom > other.top   + tolerance)

    def distance_to(self, other: "BoundingBox") -> float:
        """Minimum axis-aligned gap between two boxes (0 if touching/overlapping)."""
        dx = max(0, max(self.left, other.left) - min(self.right, other.right))
        dy = max(0, max(self.top,  other.top)  - min(self.bottom, other.bottom))
        return (dx ** 2 + dy ** 2) ** 0.5

    # ── Transforms ───────────────────────────────────────────────────────────

    def translate(self, dx: float = 0, dy: float = 0) -> "BoundingBox":
        return BoundingBox(self.x + dx, self.y + dy, self.width, self.height, self.node_id)

    def moved_to(self, x: float, y: float) -> "BoundingBox":
        return BoundingBox(x, y, self.width, self.height, self.node_id)

    def padded(self, pad: float) -> "BoundingBox":
        return BoundingBox(self.x - pad, self.y - pad,
                           self.width + 2 * pad, self.height + 2 * pad, self.node_id)

    def inset(self, left: float = 0, right: float = 0,
              top: float = 0, bottom: float = 0) -> "BoundingBox":
        return BoundingBox(self.x + left, self.y + top,
                           max(0.0, self.width  - left - right),
                           max(0.0, self.height - top  - bottom),
                           self.node_id)

    # ── Construction helpers ──────────────────────────────────────────────────

    @classmethod
    def from_tuple(cls, t: tuple[float, float, float, float], node_id: str = "") -> "BoundingBox":
        """Convert legacy (x, y, w, h) tuple."""
        return cls(*t, node_id=node_id)

    @classmethod
    def from_region(cls, d: dict, node_id: str = "") -> "BoundingBox":
        return cls(float(d["x"]), float(d["y"]),
                   float(d["width"]), float(d["height"]), node_id)

    def to_region(self) -> dict:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    def __repr__(self) -> str:
        return (f"BoundingBox({self.node_id!r}: "
                f"x={self.x:.1f} y={self.y:.1f} w={self.width:.1f} h={self.height:.1f})")

    # ── Union ─────────────────────────────────────────────────────────────────

    @classmethod
    def union(cls, boxes: list["BoundingBox"]) -> Optional["BoundingBox"]:
        """Smallest BoundingBox enclosing all given boxes."""
        if not boxes:
            return None
        xs = [b.x for b in boxes];  rs = [b.right  for b in boxes]
        ys = [b.y for b in boxes];  bs = [b.bottom for b in boxes]
        return cls(min(xs), min(ys), max(rs) - min(xs), max(bs) - min(ys))
