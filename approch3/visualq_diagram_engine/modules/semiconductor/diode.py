"""
DiodeModule — higher-level diode diagram builder.

Phase 2 scope:
- Diode symbol (triangle + bar) rendered as a standalone circuit element
- IV characteristic curve (forward/reverse regions)
- Zener diode variant with breakdown knee
- LED variant with photon emission arrows
- Photodiode variant with incident light arrows

This module will compose PNJunction + circuit primitives to render
complete diode circuit diagrams including the diode symbol, voltage/current
labels, and operating point annotation.
"""

from visualq_diagram_engine.core.scene import Scene


class DiodeModule:
    """Diode diagram builder (Phase 2)."""

    def build_symbol_scene(self) -> Scene:
        """Render a standalone diode circuit symbol. Not yet implemented."""
        raise NotImplementedError("DiodeModule is planned for Phase 2")

    def build_iv_curve_scene(self) -> Scene:
        """Render the I-V characteristic curve. Not yet implemented."""
        raise NotImplementedError("DiodeModule is planned for Phase 2")
