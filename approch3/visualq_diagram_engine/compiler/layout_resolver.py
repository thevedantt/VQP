"""
LayoutResolver — pre-processes a diagram spec that contains a `layout:` section.

Runs BEFORE the SceneBuilder so the SceneBuilder receives a fully resolved spec
with explicit positions — it never needs to know about layout.

A spec may contain::

    layout:
      canvas:
        width: 900
        height: 480
      semiconductor:
        margin_x: 85
        margin_y: 75
        block_height: 165
        proportions:
          p: 40        # percent
          depletion: 14
          n: 46
      circuit:
        baseline_y: 290     # y of bottom circuit rail
        arm_x_margin: 42    # px beyond P/N contacts for outer arms
        switch_length: 55
        battery_cells: 1
        battery_gap: 18     # gap between switch exit and battery
        resistor_length: 80

When the resolver runs it:
  1. Builds a SemiconductorLayout from `layout.semiconductor`
  2. Builds a CircuitLayout  from `layout.circuit`
  3. Injects computed `scene.regions`
  4. Overrides `scene.width`/`scene.height` if `layout.canvas` is present
  5. For each layer object that has `layout_circuit_id:`, fills in the
     concrete position (x/y or waypoints) from the CircuitLayout

If no `layout:` key is present the spec is returned unchanged.
"""

import copy
import logging
from typing import Any, Optional, Type

from visualq_diagram_engine.layouts.semiconductor_layout import (
    SemiconductorLayout,
    CircuitLayout,
)
from visualq_diagram_engine.layouts.collision_detector import CollisionDetector
from visualq_diagram_engine.theme.base_theme import BaseTheme

logger = logging.getLogger(__name__)


class LayoutResolver:
    def __init__(self, theme: type[BaseTheme] | None = None) -> None:
        from visualq_diagram_engine.theme.ncert_theme import NCERTTheme
        self._theme: type[BaseTheme] = theme or NCERTTheme

    def resolve(self, spec: dict) -> dict:
        """Resolve layout declarations into explicit positions."""
        if "layout" not in spec:
            return spec

        spec = copy.deepcopy(spec)
        layout = spec["layout"]

        canvas_w = float(spec["scene"].get("width", 900))
        canvas_h = float(spec["scene"].get("height", 480))

        # 1. Override canvas from layout.canvas
        if "canvas" in layout:
            canvas_w = float(layout["canvas"].get("width", canvas_w))
            canvas_h = float(layout["canvas"].get("height", canvas_h))
            spec["scene"]["width"]  = canvas_w
            spec["scene"]["height"] = canvas_h

        # 2. Build SemiconductorLayout
        semi_layout: SemiconductorLayout | None = None
        circ_layout: CircuitLayout | None = None

        if "semiconductor" in layout:
            semi_layout = self._build_semi_layout(layout["semiconductor"], canvas_w, canvas_h)
            # Inject computed regions (p_region, depletion, n_region + full semiconductor box)
            regions = semi_layout.as_regions()
            regions["semiconductor"] = semi_layout.full_box.to_region()
            spec["scene"]["regions"] = regions
            logger.debug(
                "LayoutResolver: semiconductor regions computed "
                "(p_w=%.0f dep_w=%.0f n_w=%.0f)",
                semi_layout.p_box.width, semi_layout.dep_box.width, semi_layout.n_box.width,
            )

            # 3. Build CircuitLayout
            if "circuit" in layout:
                circ_layout = self._build_circuit_layout(
                    layout["circuit"], semi_layout, canvas_h
                )
                logger.debug(
                    "LayoutResolver: circuit y=%.0f switch_x=%.0f battery_x=%.0f resistor_x=%.0f",
                    circ_layout.circuit_y, circ_layout.switch_x,
                    circ_layout.battery_x, circ_layout.resistor_x,
                )

            # 4. Validate
            cd = CollisionDetector(canvas_w, canvas_h)
            cd.check_regions(spec["scene"]["regions"])
            if circ_layout:
                cd.check_caption(
                    float(layout.get("caption_y", canvas_h - 20)),
                    bottom_margin=10,
                )

        # 5. Inject positions into layer objects
        if circ_layout is not None:
            for layer in spec.get("layers", []):
                new_objects: list[dict] = []
                for obj in layer.get("objects", []):
                    resolved = self._resolve_object(obj, semi_layout, circ_layout, canvas_w, canvas_h)
                    new_objects.append(resolved)
                layer["objects"] = new_objects

        return spec

    # ── private: build layout models ─────────────────────────────────────────

    def _build_semi_layout(self, semi: dict, canvas_w: float, canvas_h: float) -> SemiconductorLayout:
        t = self._theme
        props = semi.get("proportions", {})
        p_frac   = float(props.get("p",         t.semi_p_frac   * 100)) / 100
        dep_frac = float(props.get("depletion", t.semi_dep_frac * 100)) / 100
        n_frac   = float(props.get("n",         t.semi_n_frac   * 100)) / 100
        # Normalise so they always sum to 1
        total = p_frac + dep_frac + n_frac
        if abs(total - 1.0) > 0.001:
            p_frac /= total; dep_frac /= total; n_frac /= total
        return SemiconductorLayout(
            canvas_w     = canvas_w,
            canvas_h     = canvas_h,
            margin_x     = float(semi.get("margin_x",     t.semi_margin_x)),
            margin_y     = float(semi.get("margin_y",     t.semi_margin_y)),
            block_height = float(semi.get("block_height", t.semi_height)),
            p_fraction   = p_frac,
            dep_fraction = dep_frac,
            n_fraction   = n_frac,
        )

    def _build_circuit_layout(
        self, circ: dict, semi: SemiconductorLayout, canvas_h: float
    ) -> CircuitLayout:
        t = self._theme
        baseline_y = float(circ.get("baseline_y", semi.bottom_y + t.circuit_gap))
        return CircuitLayout(
            semi             = semi,
            circuit_y        = baseline_y,
            arm_x_margin     = float(circ.get("arm_x_margin",    t.circuit_arm_margin)),
            switch_length    = float(circ.get("switch_length",    t.switch_length)),
            battery_cells    = int(circ.get("battery_cells",     1)),
            battery_gap      = float(circ.get("battery_gap",     t.battery_gap)),
            resistor_length  = float(circ.get("resistor_length", t.resistor_length)),
        )

    # ── private: object resolver ─────────────────────────────────────────────

    def _resolve_object(
        self,
        obj: dict,
        semi: SemiconductorLayout | None,
        circ: CircuitLayout | None,
        canvas_w: float,
        canvas_h: float,
    ) -> dict:
        layout_id = obj.get("layout_circuit_id")
        if layout_id is None or circ is None:
            return obj

        obj = dict(obj)   # shallow copy — we're filling in positions
        t = obj.get("type", "")

        if layout_id == "switch":
            obj.update(circ.switch_pos())

        elif layout_id == "battery":
            obj.update(circ.battery_pos())

        elif layout_id == "resistor":
            obj.update(circ.resistor_pos())

        elif layout_id == "wire_left_arm":
            obj["waypoints"] = circ.wire_left_arm

        elif layout_id == "wire_switch_to_battery":
            obj["waypoints"] = circ.wire_switch_to_battery

        elif layout_id == "wire_battery_to_resistor":
            obj["waypoints"] = circ.wire_battery_to_resistor

        elif layout_id == "wire_right_arm":
            obj["waypoints"] = circ.wire_right_arm

        elif layout_id == "label_e":
            # External field E arrow — spans full semiconductor at upper y
            if semi:
                obj["start_x"] = semi.p_box.x + 14
                obj["start_y"] = semi.block_y + semi.block_height * 0.35
                obj["end_x"]   = semi.n_box.right - 14
                obj["end_y"]   = semi.block_y + semi.block_height * 0.35

        elif layout_id == "label_ei":
            # Internal field Ei — spans depletion at lower y
            if semi:
                dep = semi.dep_box
                obj["start_x"] = dep.right - 10
                obj["start_y"] = semi.block_y + semi.block_height * 0.65
                obj["end_x"]   = dep.x + 10
                obj["end_y"]   = semi.block_y + semi.block_height * 0.65

        elif layout_id == "caption":
            obj["x"] = canvas_w / 2
            obj["y"] = canvas_h - 18

        elif layout_id == "title":
            obj["x"] = canvas_w / 2
            obj["y"] = float(obj.get("y", 30))

        else:
            logger.warning("LayoutResolver: unknown layout_circuit_id '%s'", layout_id)

        return obj
