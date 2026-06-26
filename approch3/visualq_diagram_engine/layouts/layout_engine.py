"""
Core layout engine: Box, HStack, VStack, Spacer, and LayoutEngine.

These are data structures that describe layout intentions.
Positions are computed by the layout engine and injected into the spec
before the SceneBuilder runs — keeping the renderer unchanged.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ── Box ───────────────────────────────────────────────────────────────────────

@dataclass
class Box:
    """Rectangular region with derived anchor points."""
    x: float
    y: float
    width: float
    height: float
    label: str = ""

    @property
    def cx(self) -> float:       return self.x + self.width / 2
    @property
    def cy(self) -> float:       return self.y + self.height / 2
    @property
    def right(self) -> float:    return self.x + self.width
    @property
    def bottom(self) -> float:   return self.y + self.height
    @property
    def top(self) -> float:      return self.y
    @property
    def left(self) -> float:     return self.x

    # ── Derived boxes ──────────────────────────────────────────────────────
    def padded(self, margin: float) -> Box:
        """Inset box by a uniform margin."""
        return Box(self.x + margin, self.y + margin,
                   max(0.0, self.width  - 2 * margin),
                   max(0.0, self.height - 2 * margin),
                   self.label)

    def inset(self, left: float = 0, right: float = 0,
              top: float = 0, bottom: float = 0) -> Box:
        return Box(self.x + left, self.y + top,
                   max(0.0, self.width  - left - right),
                   max(0.0, self.height - top  - bottom),
                   self.label)

    def with_height(self, h: float) -> Box:
        return Box(self.x, self.y, self.width, h, self.label)

    def translate(self, dx: float = 0, dy: float = 0) -> Box:
        return Box(self.x + dx, self.y + dy, self.width, self.height, self.label)

    # ── Region-dict interop (matches scene.regions format) ─────────────────
    def to_region(self) -> dict:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @classmethod
    def from_region(cls, d: dict, label: str = "") -> Box:
        return cls(float(d["x"]), float(d["y"]),
                   float(d["width"]), float(d["height"]), label)

    # ── Anchor points ──────────────────────────────────────────────────────
    def anchor(self, name: str) -> tuple[float, float]:
        anchors = {
            "tl": (self.x,    self.y),
            "tc": (self.cx,   self.y),
            "tr": (self.right, self.y),
            "ml": (self.x,    self.cy),
            "mc": (self.cx,   self.cy),
            "mr": (self.right, self.cy),
            "bl": (self.x,    self.bottom),
            "bc": (self.cx,   self.bottom),
            "br": (self.right, self.bottom),
        }
        return anchors[name]


# ── HStack ────────────────────────────────────────────────────────────────────

def hstack(
    boxes: list[Box],
    gap: float = 0,
    origin: tuple[float, float] = (0.0, 0.0),
    height: Optional[float] = None,
) -> list[Box]:
    """Lay out boxes in a horizontal row from `origin`, with `gap` between them."""
    cx, y = origin
    result: list[Box] = []
    for b in boxes:
        h = height if height is not None else b.height
        result.append(Box(cx, y, b.width, h, b.label))
        cx += b.width + gap
    return result


def hstack_fractional(
    fractions: list[float],
    labels: list[str],
    total_width: float,
    x: float, y: float, height: float,
    gap: float = 0,
) -> list[Box]:
    """Build HStack from fractional widths that sum to 1.0.

    Returns one Box per fraction with computed widths that fill total_width
    (gaps are subtracted from available width).
    """
    n = len(fractions)
    total_gap = gap * max(n - 1, 0)
    avail = total_width - total_gap
    boxes: list[Box] = []
    cx = x
    for i, (frac, label) in enumerate(zip(fractions, labels)):
        w = avail * frac
        boxes.append(Box(cx, y, w, height, label))
        cx += w + (gap if i < n - 1 else 0)
    return boxes


# ── VStack ────────────────────────────────────────────────────────────────────

def vstack(
    boxes: list[Box],
    gap: float = 0,
    origin: tuple[float, float] = (0.0, 0.0),
    width: Optional[float] = None,
) -> list[Box]:
    x, cy = origin
    result: list[Box] = []
    for b in boxes:
        w = width if width is not None else b.width
        result.append(Box(x, cy, w, b.height, b.label))
        cy += b.height + gap
    return result


# ── Bounding box helpers ─────────────────────────────────────────────────────

def union_boxes(boxes: list[Box]) -> Optional[Box]:
    """Return smallest Box containing all given boxes."""
    if not boxes:
        return None
    xs = [b.x for b in boxes]
    ys = [b.y for b in boxes]
    rs = [b.right for b in boxes]
    bs = [b.bottom for b in boxes]
    return Box(min(xs), min(ys), max(rs) - min(xs), max(bs) - min(ys))


def center_box_in(inner: Box, outer: Box) -> Box:
    """Translate inner box so it is centred inside outer box."""
    dx = outer.cx - inner.cx
    dy = outer.cy - inner.cy
    return inner.translate(dx, dy)
