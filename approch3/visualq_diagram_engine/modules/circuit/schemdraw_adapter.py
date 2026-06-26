"""
SchemdrawAdapter — optional adapter to import schemdraw circuit drawings
into the VisualQ scene graph.

Phase 2 scope:
- Accept a schemdraw.Drawing object
- Extract element positions and paths
- Convert to VisualQ Line, BezierPath, Text, and Group primitives
- Enables schemdraw as an optional circuit-layout backend while keeping
  the VisualQ rendering pipeline deterministic

schemdraw is a third-party library (pip install schemdraw) and is NOT
a required dependency. This adapter gracefully fails if not installed.
"""

from visualq_diagram_engine.core.scene import Scene


class SchemdrawAdapter:
    """Converts a schemdraw drawing to a VisualQ Scene (Phase 2)."""

    def convert(self, drawing) -> Scene:
        """Convert schemdraw.Drawing to a VisualQ Scene."""
        try:
            import schemdraw  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "schemdraw is not installed. Install it with: pip install schemdraw"
            ) from exc
        raise NotImplementedError("SchemdrawAdapter is planned for Phase 2")
