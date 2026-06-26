"""
ConstraintSolver — resolve positional constraints between named bounding boxes.

Supports 15 spatial constraints for scientific diagram layout.
Uses iterative dependency resolution (no circular constraints expected).

Usage::

    solver = ConstraintSolver()
    solver.register("semiconductor", BoundingBox(85, 75, 730, 165))
    solver.register("battery_e",     BoundingBox(0, 0, 40, 40))  # unknown pos

    solver.add("battery_e",  "place_right_of", target="switch_k",  gap=18)
    solver.add("battery_e",  "align_center_y", target="switch_k")
    solver.add("caption",    "place_below",     target="circuit_row", gap=20)
    solver.add("caption",    "center_h",        target="semiconductor")

    resolved = solver.solve()   # {node_id: BoundingBox}
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional

from visualq_diagram_engine.layout.bounding_box import BoundingBox

logger = logging.getLogger(__name__)

# ── Constraint dataclass ──────────────────────────────────────────────────────

@dataclass
class Constraint:
    """A single positional constraint on a node relative to a target."""
    kind: str               # constraint type (see SUPPORTED below)
    target: str             # id of the reference node
    gap: float = 0.0        # pixel gap (for place_* constraints)
    offset_x: float = 0.0  # additional x offset
    offset_y: float = 0.0  # additional y offset


SUPPORTED_CONSTRAINTS = {
    # Placement (move node so it is outside target)
    "place_below",        # top of node = bottom of target + gap
    "place_above",        # bottom of node = top of target - gap
    "place_right_of",     # left of node = right of target + gap
    "place_left_of",      # right of node = left of target - gap

    # Alignment (keep node's edge / center aligned with target)
    "align_top",          # node.top  = target.top
    "align_bottom",       # node.bottom = target.bottom
    "align_left",         # node.left  = target.left
    "align_right",        # node.right = target.right
    "align_center_x",     # node.cx = target.cx
    "align_center_y",     # node.cy = target.cy

    # Centering inside target
    "center_in",          # center both axes inside target
    "center_h",           # center horizontally inside target (keep y)
    "center_v",           # center vertically inside target (keep x)

    # Size matching
    "match_width",        # node.width  = target.width
    "match_height",       # node.height = target.height
}


# ── Solver ────────────────────────────────────────────────────────────────────

class ConstraintSolver:
    """
    Topological constraint resolver for named bounding boxes.

    Nodes whose positions are fully known (registered with a concrete box)
    are 'resolved' from the start.  Nodes with constraints are resolved
    as soon as all their targets are resolved.  The solver iterates until
    convergence or a maximum number of passes.
    """

    MAX_PASSES = 20

    def __init__(self) -> None:
        self._boxes: dict[str, BoundingBox] = {}        # known boxes
        self._pending: dict[str, BoundingBox] = {}      # unresolved (x=0,y=0 placeholder)
        self._constraints: dict[str, list[Constraint]] = {}  # node_id → constraints

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, node_id: str, box: BoundingBox) -> None:
        """Register a node with a known position (anchor node)."""
        self._boxes[node_id] = box

    def register_unknown(self, node_id: str, width: float, height: float) -> None:
        """Register a node whose position will be determined by constraints."""
        self._pending[node_id] = BoundingBox(0, 0, width, height, node_id)

    def add(self, node_id: str, kind: str, **kwargs) -> None:
        """
        Add a constraint on node_id.

        Keyword arguments become fields on the Constraint dataclass.
        Examples::
            solver.add("battery_e", "place_right_of", target="switch_k", gap=18)
            solver.add("caption",   "center_h",       target="semiconductor")
        """
        if kind not in SUPPORTED_CONSTRAINTS:
            logger.warning("ConstraintSolver: unknown constraint '%s' — ignored", kind)
            return
        c = Constraint(kind=kind, **kwargs)
        self._constraints.setdefault(node_id, []).append(c)

    # ── Solve ─────────────────────────────────────────────────────────────────

    def solve(self) -> dict[str, BoundingBox]:
        """
        Resolve all constraints and return a complete {node_id: BoundingBox} dict.

        Resolved boxes incorporate both registered anchors and newly computed boxes.
        """
        resolved = dict(self._boxes)
        pending  = dict(self._pending)

        for pass_num in range(self.MAX_PASSES):
            progress = False
            for node_id, box in list(pending.items()):
                constraints = self._constraints.get(node_id, [])
                # Check if all targets are resolved
                if not all(c.target in resolved for c in constraints):
                    continue  # wait for next pass
                # Apply all constraints to get the final position
                new_box = self._apply_constraints(box, constraints, resolved)
                resolved[node_id] = new_box
                del pending[node_id]
                progress = True

            if not pending:
                break
            if not progress:
                # Log which nodes are stuck
                for nid in pending:
                    missing = [c.target for c in self._constraints.get(nid, [])
                               if c.target not in resolved]
                    logger.warning(
                        "ConstraintSolver: '%s' waiting on unresolved targets %s",
                        nid, missing,
                    )
                break

        if pending:
            logger.warning(
                "ConstraintSolver: %d node(s) unresolved after %d passes: %s",
                len(pending), self.MAX_PASSES, list(pending),
            )
            resolved.update(pending)   # emit with (0,0) position

        logger.debug("ConstraintSolver: resolved %d nodes in ≤%d passes",
                     len(resolved), pass_num + 1)
        return resolved

    # ── Internal constraint application ───────────────────────────────────────

    def _apply_constraints(
        self,
        box: BoundingBox,
        constraints: list[Constraint],
        resolved: dict[str, BoundingBox],
    ) -> BoundingBox:
        x, y = box.x, box.y
        w, h = box.width, box.height

        for c in constraints:
            t = resolved[c.target]   # guaranteed resolved by caller

            if c.kind == "place_below":
                y = t.bottom + c.gap + c.offset_y
                x = x + c.offset_x

            elif c.kind == "place_above":
                y = t.top - h - c.gap + c.offset_y
                x = x + c.offset_x

            elif c.kind == "place_right_of":
                x = t.right + c.gap + c.offset_x
                y = y + c.offset_y

            elif c.kind == "place_left_of":
                x = t.left - w - c.gap + c.offset_x
                y = y + c.offset_y

            elif c.kind == "align_top":
                y = t.top + c.offset_y

            elif c.kind == "align_bottom":
                y = t.bottom - h + c.offset_y

            elif c.kind == "align_left":
                x = t.left + c.offset_x

            elif c.kind == "align_right":
                x = t.right - w + c.offset_x

            elif c.kind == "align_center_x":
                x = t.cx - w / 2 + c.offset_x

            elif c.kind == "align_center_y":
                y = t.cy - h / 2 + c.offset_y

            elif c.kind == "center_in":
                x = t.cx - w / 2 + c.offset_x
                y = t.cy - h / 2 + c.offset_y

            elif c.kind == "center_h":
                x = t.cx - w / 2 + c.offset_x

            elif c.kind == "center_v":
                y = t.cy - h / 2 + c.offset_y

            elif c.kind == "match_width":
                w = t.width

            elif c.kind == "match_height":
                h = t.height

        return BoundingBox(x, y, w, h, box.node_id)
