"""Spacing utilities — distribute nodes evenly and apply margins."""

from visualq_diagram_engine.core.scene import SceneNode


def distribute_evenly(
    nodes: list[SceneNode],
    axis: str,
    start: float,
    end: float,
) -> None:
    """
    Distribute nodes evenly along an axis between start and end.

    axis: 'x' or 'y'
    start, end: the range to distribute within (using node anchor positions)
    """
    if len(nodes) < 2:
        return
    count = len(nodes)
    step = (end - start) / (count - 1)
    for i, node in enumerate(nodes):
        x, y = node.position
        if axis == "x":
            node.position = (start + i * step, y)
        else:
            node.position = (x, start + i * step)


def apply_margin(node: SceneNode, margin: float) -> None:
    """Shift a node inward by margin on all sides (adjusts position only)."""
    x, y = node.position
    node.position = (x + margin, y + margin)


def pad_group(
    nodes: list[SceneNode],
    padding_x: float,
    padding_y: float,
) -> None:
    """Apply uniform padding to all nodes in a group relative to the group origin."""
    if not nodes:
        return
    min_x = min(node.position[0] for node in nodes)
    min_y = min(node.position[1] for node in nodes)
    for node in nodes:
        x, y = node.position
        node.position = (x - min_x + padding_x, y - min_y + padding_y)
