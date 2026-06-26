"""Text primitive."""

from dataclasses import dataclass
from visualq_diagram_engine.core.scene import SceneNode


@dataclass
class Text(SceneNode):
    content: str = ""

    def render(self, canvas) -> None:
        attrs = self.style.to_text_attrs()
        x, y = self.position
        elem = canvas.text(self.content, insert=(x, y), **attrs)
        canvas.add(elem)

    def bounding_box(self) -> tuple[float, float, float, float]:
        x, y = self.position
        approx_w = len(self.content) * self.style.font_size * 0.6
        return (x, y - self.style.font_size, approx_w, self.style.font_size)
