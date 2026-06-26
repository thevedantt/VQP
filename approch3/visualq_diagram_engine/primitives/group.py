"""Group primitive — contains and renders child SceneNodes."""

from dataclasses import dataclass, field
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class Group(SceneNode):
    children: list[SceneNode] = field(default_factory=list)

    def add(self, node: SceneNode) -> None:
        self.children.append(node)

    def render(self, canvas) -> None:
        for child in self.children:
            if child.visible:
                child.render(canvas)

    def bounding_box(self) -> tuple[float, float, float, float]:
        if not self.children:
            return (0.0, 0.0, 0.0, 0.0)
        boxes = [c.bounding_box() for c in self.children]
        x = min(b[0] for b in boxes)
        y = min(b[1] for b in boxes)
        max_x = max(b[0] + b[2] for b in boxes)
        max_y = max(b[1] + b[3] for b in boxes)
        return (x, y, max_x - x, max_y - y)
