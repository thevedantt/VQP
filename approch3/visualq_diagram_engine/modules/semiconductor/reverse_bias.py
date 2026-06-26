"""
ReverseBiasBuilder — stub for reverse-biased PN junction diagrams.

Reverse bias: external battery connected with - to P and + to N.
This widens the depletion region and prevents conventional current flow
(only a tiny reverse saturation current due to minority carriers).
The diagram will show: wider depletion region, carriers moving away from
the junction, and a larger built-in electric field arrow.
"""

from visualq_diagram_engine.core.scene import Scene
from visualq_diagram_engine.modules.semiconductor.pn_junction import PNJunction


class ReverseBiasBuilder(PNJunction):
    """
    Programmatic builder for reverse-biased PN junction scenes.

    TODO (Phase 2):
    - Widen depletion region proportional to reverse voltage
    - Show minority carrier drift arrows (tiny, opposite direction)
    - Add reverse battery connection labels
    - Show breakdown region for Zener diode variant
    """

    def build(self) -> Scene:
        """Build reverse-bias scene. Not yet implemented — returns base scene."""
        scene = self.build_scene("Reverse Biased PN Junction")
        return scene
