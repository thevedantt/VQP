"""Spacing helpers — distribute boxes evenly, compute gaps."""

from __future__ import annotations
from visualq_diagram_engine.layout.bounding_box import BoundingBox


def distribute_h(
    boxes: list[BoundingBox],
    container_x: float,
    container_w: float,
    gap: float | None = None,
) -> list[BoundingBox]:
    """
    Distribute boxes horizontally within a container.

    If `gap` is provided, place boxes with that fixed gap between them.
    Otherwise, space them evenly to fill container_w.
    Returns new BoundingBox list with updated x coordinates.
    """
    if not boxes:
        return []
    total_w = sum(b.width for b in boxes)
    n = len(boxes)
    if gap is not None:
        actual_gap = gap
    else:
        actual_gap = (container_w - total_w) / max(n - 1, 1) if n > 1 else 0.0
    result = []
    cx = container_x
    for b in boxes:
        result.append(BoundingBox(cx, b.y, b.width, b.height, b.node_id))
        cx += b.width + actual_gap
    return result


def distribute_v(
    boxes: list[BoundingBox],
    container_y: float,
    container_h: float,
    gap: float | None = None,
) -> list[BoundingBox]:
    """Distribute boxes vertically within a container."""
    if not boxes:
        return []
    total_h = sum(b.height for b in boxes)
    n = len(boxes)
    if gap is not None:
        actual_gap = gap
    else:
        actual_gap = (container_h - total_h) / max(n - 1, 1) if n > 1 else 0.0
    result = []
    cy = container_y
    for b in boxes:
        result.append(BoundingBox(b.x, cy, b.width, b.height, b.node_id))
        cy += b.height + actual_gap
    return result


def equal_gap_h(total_w: float, item_widths: list[float]) -> float:
    """Return the equal gap between items to fill total_w."""
    n = len(item_widths)
    return (total_w - sum(item_widths)) / max(n - 1, 1) if n > 1 else 0.0


def equal_gap_v(total_h: float, item_heights: list[float]) -> float:
    return (total_h - sum(item_heights)) / max(len(item_heights) - 1, 1)
