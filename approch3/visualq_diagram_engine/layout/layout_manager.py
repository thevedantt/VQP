"""
LayoutManager — top-level orchestrator for the constraint-based layout system.

Combines the ConstraintSolver with layout containers (HBox, VBox, Grid) to
produce a fully resolved {node_id: BoundingBox} dict ready for the renderer.

The LayoutManager replaces all manual coordinate calculations.
It is the single place where geometry is computed — the renderer only draws.

Usage (programmatic)::

    from visualq_diagram_engine.layout.layout_manager import LayoutManager
    from visualq_diagram_engine.layout.bounding_box import BoundingBox
    from visualq_diagram_engine.theme.ncert_theme import NCERTTheme

    mgr = LayoutManager(theme=NCERTTheme)
    mgr.register("semiconductor", BoundingBox(85, 75, 730, 165))
    mgr.add_constraint("caption", "place_below", target="semiconductor", gap=200)
    mgr.add_constraint("caption", "center_h",    target="semiconductor")
    result = mgr.solve()   # {"semiconductor": BoundingBox(...), "caption": BoundingBox(...)}

Integration with compiler::

    The LayoutResolver calls LayoutManager internally to resolve positions,
    then injects them into the spec before SceneBuilder runs.
"""

from __future__ import annotations
import logging
from typing import Optional, Type

from visualq_diagram_engine.layout.bounding_box import BoundingBox
from visualq_diagram_engine.layout.constraint_solver import ConstraintSolver
from visualq_diagram_engine.layout.base_layout import LayoutNode

logger = logging.getLogger(__name__)


class LayoutManager:
    """
    Orchestrates constraint solving + container layout for a single diagram.

    Acts as a façade: callers interact with named nodes; the manager routes
    to either the ConstraintSolver (for position constraints) or layout
    containers (for grouping/stacking).
    """

    def __init__(self, theme=None) -> None:
        self._theme = theme
        self._solver = ConstraintSolver()
        self._containers: dict[str, LayoutNode] = {}
        self._resolved: dict[str, BoundingBox] = {}

    # ── Node registration ─────────────────────────────────────────────────────

    def register(self, node_id: str, box: BoundingBox) -> "LayoutManager":
        """Register a node with a known (fixed) bounding box."""
        self._solver.register(node_id, box)
        return self

    def register_size(self, node_id: str, width: float, height: float) -> "LayoutManager":
        """Register a node whose position will be determined by constraints."""
        self._solver.register_unknown(node_id, width, height)
        return self

    def add_container(self, container: LayoutNode) -> "LayoutManager":
        """Add a pre-built layout container (HBox, VBox, etc.)."""
        self._containers[container.node_id] = container
        return self

    # ── Constraints ───────────────────────────────────────────────────────────

    def add_constraint(self, node_id: str, kind: str, **kwargs) -> "LayoutManager":
        """Add a positional constraint.  See ConstraintSolver.add() for details."""
        self._solver.add(node_id, kind, **kwargs)
        return self

    # ── Solve ─────────────────────────────────────────────────────────────────

    def solve(self) -> dict[str, BoundingBox]:
        """
        Run the constraint solver, apply container layouts, and return
        the complete resolved {node_id: BoundingBox} mapping.
        """
        # 1. Solve positional constraints
        self._resolved = self._solver.solve()

        # 2. Apply any pre-built containers at their resolved origins
        for cid, container in self._containers.items():
            if cid in self._resolved:
                origin = self._resolved[cid]
                placements = container.apply(origin.x, origin.y)
                for pid, bb in placements:
                    self._resolved[pid] = bb
            else:
                logger.warning("LayoutManager: container '%s' has no resolved origin", cid)

        logger.debug("LayoutManager: resolved %d layout nodes", len(self._resolved))
        return self._resolved

    # ── Query ─────────────────────────────────────────────────────────────────

    def get(self, node_id: str) -> Optional[BoundingBox]:
        """Return a resolved bounding box by node id."""
        return self._resolved.get(node_id)

    def validate(self, canvas_w: float, canvas_h: float) -> list[str]:
        """
        Run layout validation.  Returns list of warning strings.
        Does NOT modify layout — only inspects.
        """
        canvas = BoundingBox(0, 0, canvas_w, canvas_h, "canvas")
        warnings: list[str] = []
        boxes = list(self._resolved.values())

        for bb in boxes:
            if not canvas.contains(bb, tolerance=5):
                warnings.append(
                    f"Node '{bb.node_id}' extends outside canvas "
                    f"(right={bb.right:.0f} bottom={bb.bottom:.0f})"
                )

        ids = [b.node_id for b in boxes]
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if boxes[i].overlaps(boxes[j], tolerance=2):
                    warnings.append(
                        f"Nodes '{ids[i]}' and '{ids[j]}' overlap"
                    )

        for w in warnings:
            logger.warning("LayoutManager validation: %s", w)
        return warnings
