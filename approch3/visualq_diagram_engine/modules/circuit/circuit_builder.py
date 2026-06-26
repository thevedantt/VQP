"""
CircuitBuilder — builds circuit diagrams from component specs.

Phase 2 scope:
- Parse a list of circuit components (resistor, capacitor, inductor,
  voltage source, current source, diode, transistor, op-amp)
- Route wires using a grid-based topology
- Place component symbols at specified nodes
- Label nodes with voltage/current annotations
- Support series, parallel, and bridge configurations

Components will be rendered as SVG primitive groups using standardized
IEC/IEEE schematic symbols. No external circuit simulation is performed.
"""

from visualq_diagram_engine.core.scene import Scene


class CircuitBuilder:
    """Grid-based circuit diagram builder (Phase 2)."""

    def build(self, spec: dict) -> Scene:
        """Build a circuit scene from a component specification dict."""
        raise NotImplementedError("CircuitBuilder is planned for Phase 2")
