"""
layout — constraint-based layout engine for scientific diagrams.

Import from here for all layout needs::

    from visualq_diagram_engine.layout import (
        BoundingBox,
        ConstraintSolver, LayoutManager,
        HBox, VBox, GridLayout, AnchorLayout,
        Padding, Margin, Spacer, LeafNode,
        HAlign, VAlign,
        distribute_h, distribute_v,
    )
"""

from visualq_diagram_engine.layout.bounding_box import BoundingBox
from visualq_diagram_engine.layout.alignment import HAlign, VAlign, align_x, align_y
from visualq_diagram_engine.layout.spacing import distribute_h, distribute_v, equal_gap_h, equal_gap_v
from visualq_diagram_engine.layout.base_layout import LayoutNode, LeafNode, Spacer
from visualq_diagram_engine.layout.hbox import HBox
from visualq_diagram_engine.layout.vbox import VBox
from visualq_diagram_engine.layout.grid_layout import GridLayout
from visualq_diagram_engine.layout.anchor_layout import AnchorLayout
from visualq_diagram_engine.layout.padding import Padding, Margin
from visualq_diagram_engine.layout.constraint_solver import ConstraintSolver, Constraint, SUPPORTED_CONSTRAINTS
from visualq_diagram_engine.layout.layout_manager import LayoutManager

__all__ = [
    "BoundingBox",
    "HAlign", "VAlign", "align_x", "align_y",
    "distribute_h", "distribute_v", "equal_gap_h", "equal_gap_v",
    "LayoutNode", "LeafNode", "Spacer",
    "HBox", "VBox", "GridLayout", "AnchorLayout",
    "Padding", "Margin",
    "ConstraintSolver", "Constraint", "SUPPORTED_CONSTRAINTS",
    "LayoutManager",
]
