"""Alignment enums and helpers for layout containers."""

from __future__ import annotations
from enum import Enum


class HAlign(Enum):
    """Horizontal alignment within a container or relative to a target."""
    LEFT   = "left"
    CENTER = "center"
    RIGHT  = "right"
    STRETCH = "stretch"


class VAlign(Enum):
    """Vertical alignment within a container or relative to a target."""
    TOP    = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    STRETCH = "stretch"


# ── String parsers ────────────────────────────────────────────────────────────

_H = {v.value: v for v in HAlign}
_V = {v.value: v for v in VAlign}


def parse_halign(s: str | HAlign) -> HAlign:
    if isinstance(s, HAlign):
        return s
    try:
        return _H[s.lower()]
    except KeyError:
        raise ValueError(f"Unknown horizontal alignment '{s}'. "
                         f"Valid: {list(_H)}")


def parse_valign(s: str | VAlign) -> VAlign:
    if isinstance(s, VAlign):
        return s
    try:
        return _V[s.lower()]
    except KeyError:
        raise ValueError(f"Unknown vertical alignment '{s}'. "
                         f"Valid: {list(_V)}")


# ── Layout helpers ────────────────────────────────────────────────────────────

def align_x(item_w: float, container_x: float, container_w: float,
            halign: HAlign) -> float:
    """Return the x coordinate that aligns item_w within the container."""
    if halign == HAlign.LEFT:
        return container_x
    if halign == HAlign.RIGHT:
        return container_x + container_w - item_w
    # CENTER or STRETCH → center
    return container_x + (container_w - item_w) / 2


def align_y(item_h: float, container_y: float, container_h: float,
            valign: VAlign) -> float:
    """Return the y coordinate that aligns item_h within the container."""
    if valign == VAlign.TOP:
        return container_y
    if valign == VAlign.BOTTOM:
        return container_y + container_h - item_h
    return container_y + (container_h - item_h) / 2
