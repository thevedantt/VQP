"""
SemiconductorLayout + CircuitLayout

Compute all positions for a PN junction diagram from high-level parameters
(proportions, margins, canvas size) rather than hardcoded coordinates.

Both classes are pure data — they only compute numbers.
They do not touch the scene graph or SVG.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from visualq_diagram_engine.layouts.layout_engine import Box, hstack_fractional


@dataclass
class SemiconductorLayout:
    """
    Computes the three-region geometry of a PN junction from proportions.

    Parameters
    ----------
    canvas_w, canvas_h : canvas size in px
    margin_x           : left/right margin between canvas edge and semiconductor block
    margin_y           : top margin above the block
    block_height       : height of the semiconductor slab
    p_fraction         : fractional width of P region  (0–1)
    dep_fraction       : fractional width of depletion  (0–1)
    n_fraction         : fractional width of N region   (0–1)
                         (the three fractions should sum to 1)
    """

    canvas_w: float = 900.0
    canvas_h: float = 480.0
    margin_x: float = 85.0
    margin_y: float = 75.0
    block_height: float = 165.0
    p_fraction: float   = 0.40
    dep_fraction: float = 0.14
    n_fraction: float   = 0.46

    # ── derived ──────────────────────────────────────────────────────────────

    @property
    def block_x(self) -> float:
        return self.margin_x

    @property
    def block_y(self) -> float:
        return self.margin_y

    @property
    def block_width(self) -> float:
        return self.canvas_w - 2 * self.margin_x

    @property
    def mid_y(self) -> float:
        return self.block_y + self.block_height / 2

    @property
    def bottom_y(self) -> float:
        return self.block_y + self.block_height

    # ── region boxes ─────────────────────────────────────────────────────────

    def _regions(self) -> list[Box]:
        return hstack_fractional(
            fractions=[self.p_fraction, self.dep_fraction, self.n_fraction],
            labels=["p_region", "depletion", "n_region"],
            total_width=self.block_width,
            x=self.block_x,
            y=self.block_y,
            height=self.block_height,
        )

    @property
    def p_box(self) -> Box:
        return self._regions()[0]

    @property
    def dep_box(self) -> Box:
        return self._regions()[1]

    @property
    def n_box(self) -> Box:
        return self._regions()[2]

    @property
    def full_box(self) -> Box:
        """Bounding box covering all three regions."""
        return Box(self.block_x, self.block_y, self.block_width, self.block_height)

    # ── connection ports (left/right contact stubs) ───────────────────────

    @property
    def p_contact(self) -> tuple[float, float]:
        """Left edge mid-point: where circuit wire meets P-side."""
        return (self.p_box.x, self.mid_y)

    @property
    def n_contact(self) -> tuple[float, float]:
        """Right edge mid-point: where circuit wire meets N-side."""
        return (self.n_box.right, self.mid_y)

    # ── scene.regions dict ───────────────────────────────────────────────────

    def as_regions(self) -> dict[str, dict]:
        return {b.label: b.to_region() for b in self._regions()}


@dataclass
class CircuitLayout:
    """
    Computes positions of all circuit components from layout parameters.

    The circuit forms a closed rectangular loop around the semiconductor:
    - Top segment: P-contact → (left arm down) → bottom rail → (right arm up) → N-contact
    - Bottom rail: switch K → battery E → long wire → resistor Rh

    All component X positions are calculated from the circuit rail y-coordinate
    and the outer arm x-offsets.
    """

    semi: SemiconductorLayout

    # rail y and outer arm x
    circuit_y: float = 295.0      # y of horizontal circuit bottom rail
    arm_x_margin: float = 42.0    # distance left of P-contact / right of N-contact

    # component widths (in px)
    switch_length: float  = 55.0
    battery_cells: int    = 1
    battery_gap: float    = 18.0   # gap between switch exit and battery entry
    battery_gap_right: float = 30.0  # gap between battery exit and resistor entry start
    resistor_length: float = 80.0
    resistor_gap: float   = 0.0   # gap from right arm to resistor exit (calculated)

    def __post_init__(self):
        if self.circuit_y == 0:
            self.circuit_y = self.semi.bottom_y + 55.0

    # ── derived x positions ──────────────────────────────────────────────────

    @property
    def _battery_cell_w(self) -> float:
        return 40.0  # BatterySymbol: BATTERY_CELL_WIDTH = 40

    @property
    def arm_left_x(self) -> float:
        return self.semi.p_contact[0] - self.arm_x_margin

    @property
    def arm_right_x(self) -> float:
        return self.semi.n_contact[0] + self.arm_x_margin

    @property
    def switch_x(self) -> float:
        return self.arm_left_x

    @property
    def switch_exit_x(self) -> float:
        return self.switch_x + self.switch_length

    @property
    def battery_x(self) -> float:
        return self.switch_exit_x + self.battery_gap

    @property
    def battery_exit_x(self) -> float:
        return self.battery_x + self._battery_cell_w * self.battery_cells

    @property
    def resistor_x(self) -> float:
        # Resistor runs right up to the outer arm, so exit aligns with arm_right_x.
        return self.arm_right_x - self.resistor_length

    @property
    def resistor_exit_x(self) -> float:
        return self.arm_right_x

    @property
    def circuit_y_pos(self) -> float:
        return self.circuit_y

    @property
    def contact_y(self) -> float:
        return self.semi.mid_y

    # ── wire waypoints ───────────────────────────────────────────────────────

    @property
    def wire_left_arm(self) -> list[list[float]]:
        """P contact → outer arm → left end of switch."""
        px, py = self.semi.p_contact
        cy = self.circuit_y
        ax = self.arm_left_x
        return [[px, py], [ax, py], [ax, cy]]

    @property
    def wire_switch_to_battery(self) -> list[list[float]]:
        cy = self.circuit_y
        return [[self.switch_exit_x, cy], [self.battery_x, cy]]

    @property
    def wire_battery_to_resistor(self) -> list[list[float]]:
        cy = self.circuit_y
        return [[self.battery_exit_x, cy], [self.resistor_x, cy]]

    @property
    def wire_right_arm(self) -> list[list[float]]:
        """Outer arm down → up to N contact.
        Starts exactly at arm_right_x (= resistor_exit_x), so there's no stub gap."""
        nx, ny = self.semi.n_contact
        cy = self.circuit_y
        ax = self.arm_right_x
        return [[ax, cy], [ax, ny], [nx, ny]]

    # ── component position dicts (for spec injection) ─────────────────────────

    def switch_pos(self) -> dict:
        return {"x": self.switch_x, "y": self.circuit_y}

    def battery_pos(self) -> dict:
        return {"x": self.battery_x, "y": self.circuit_y}

    def resistor_pos(self) -> dict:
        return {"x": self.resistor_x, "y": self.circuit_y}

    # ── label positions ──────────────────────────────────────────────────────

    def switch_label_pos(self) -> tuple[float, float]:
        cx = self.switch_x + self.switch_length / 2
        return (cx, self.circuit_y - 14)

    def battery_label_pos(self) -> tuple[float, float]:
        cx = self.battery_x + (self._battery_cell_w * self.battery_cells) / 2
        return (cx, self.circuit_y - 14)

    def resistor_label_pos(self) -> tuple[float, float]:
        cx = self.resistor_x + self.resistor_length / 2
        return (cx, self.circuit_y - 14)
