"""Alignment utilities for aligning groups of scene nodes."""

from visualq_diagram_engine.core.scene import SceneNode


def align_horizontal(nodes: list[SceneNode], y: float) -> None:
    """Set all nodes to the same y coordinate."""
    for node in nodes:
        x, _ = node.position
        node.position = (x, y)


def align_vertical(nodes: list[SceneNode], x: float) -> None:
    """Set all nodes to the same x coordinate."""
    for node in nodes:
        _, y = node.position
        node.position = (x, y)


def center_in_bounds(node: SceneNode, canvas_width: float, canvas_height: float) -> None:
    """Center a node within the given canvas dimensions using its bounding box."""
    bx, by, bw, bh = node.bounding_box()
    cx = (canvas_width - bw) / 2
    cy = (canvas_height - bh) / 2
    node.position = (cx, cy)


def align_tops(nodes: list[SceneNode]) -> None:
    """Align all nodes to the top of the topmost node's bounding box."""
    if not nodes:
        return
    top_y = min(node.bounding_box()[1] for node in nodes)
    for node in nodes:
        x, _ = node.position
        node.position = (x, top_y)


def align_lefts(nodes: list[SceneNode]) -> None:
    """Align all nodes to the leftmost node's x position."""
    if not nodes:
        return
    left_x = min(node.bounding_box()[0] for node in nodes)
    for node in nodes:
        _, y = node.position
        node.position = (left_x, y)
