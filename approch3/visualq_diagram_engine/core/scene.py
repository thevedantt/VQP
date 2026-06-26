"""Scene graph: SceneNode base class, Layer, and Scene."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from visualq_diagram_engine.primitives.styles import Style


@dataclass
class SceneNode(ABC):
    id: str
    position: tuple[float, float] = (0.0, 0.0)
    rotation: float = 0.0
    style: Style = field(default_factory=Style)
    visible: bool = True
    z_index: int = 0

    @abstractmethod
    def render(self, canvas) -> None:
        """Render this node onto the given SVGCanvas."""

    def bounding_box(self) -> tuple[float, float, float, float]:
        """Return (x, y, width, height). Override in subclasses for accuracy."""
        x, y = self.position
        return (x, y, 0.0, 0.0)

    def ports(self) -> dict[str, tuple[float, float]]:
        """
        Return named connection ports as {name: (x, y)} in canvas coordinates.

        Ports are absolute positions where wires should connect.
        Override in symbol subclasses to expose entry/exit points.
        Default: empty dict (no ports defined).
        """
        return {}

    def geometry(self):
        """
        Return a BoundingBox for this node using the layout package.
        Bridges the legacy bounding_box() tuple to the richer BoundingBox type.
        """
        from visualq_diagram_engine.layout.bounding_box import BoundingBox
        x, y, w, h = self.bounding_box()
        return BoundingBox(x, y, w, h, self.id)


@dataclass
class Layer:
    name: str
    z_index: int = 0
    objects: list[SceneNode] = field(default_factory=list)

    def add(self, node: SceneNode) -> None:
        self.objects.append(node)

    def sorted_objects(self) -> list[SceneNode]:
        return sorted(self.objects, key=lambda n: n.z_index)


@dataclass
class Scene:
    title: str
    width: float
    height: float
    background: str = "#FFFFFF"
    layers: list[Layer] = field(default_factory=list)

    def add_layer(self, layer: Layer) -> None:
        self.layers.append(layer)

    def get_layer(self, name: str) -> Optional[Layer]:
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None

    def all_objects(self) -> list[SceneNode]:
        """Return all visible objects across all layers, sorted by layer z_index then node z_index."""
        result: list[SceneNode] = []
        for layer in sorted(self.layers, key=lambda l: l.z_index):
            for node in layer.sorted_objects():
                if node.visible:
                    result.append(node)
        return result
