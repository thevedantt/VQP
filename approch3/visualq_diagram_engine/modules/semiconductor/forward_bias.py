"""ForwardBiasBuilder — programmatic builder for forward-biased PN junction."""

from visualq_diagram_engine.core.scene import Scene
from visualq_diagram_engine.modules.semiconductor.pn_junction import PNJunction


class ForwardBiasBuilder(PNJunction):
    """
    Programmatic builder for a forward-biased PN junction diagram in NCERT style.

    Forward bias: battery positive → P region, negative → N region.
    The applied field opposes and overcomes the built-in depletion field, allowing
    majority carriers to diffuse across the junction — holes drift rightward,
    electrons drift leftward, conventional current flows P→N externally.
    """

    def build(self) -> Scene:
        return self.build_forward_bias_scene()
