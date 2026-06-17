"""
circuit_renderer.py

Schema V2 renderer.
Responsibility: layout coordinates + solution → schemdraw SVG.
Does NOT calculate physics, does NOT validate, does NOT build topology.
"""

from pathlib import Path
from typing import Dict, Optional

import schemdraw
import schemdraw.elements as elm

from circuit_rules import SERIES_CIRCUITS, PARALLEL_CIRCUITS


class CircuitRenderer:

    def render(
        self,
        blueprint: Dict,
        layout: Dict,
        solution: Dict
    ) -> schemdraw.Drawing:
        circuit_type = blueprint.get("circuit_type", "")

        if circuit_type in SERIES_CIRCUITS:
            return self._draw_series(blueprint)
        elif circuit_type in PARALLEL_CIRCUITS:
            return self._draw_parallel(blueprint)
        elif circuit_type == "wheatstone_bridge":
            return self._draw_bridge(blueprint)
        elif circuit_type == "meter_bridge":
            return self._draw_meter_bridge(blueprint)
        else:
            raise ValueError(f"Unsupported circuit type: {circuit_type}")

    # ==========================================================
    # Element factory
    # ==========================================================

    def _make_element(self, comp: Optional[Dict]) -> elm.Element:
        if comp is None:
            return elm.Line()

        ctype = comp.get("type", "")
        label_text = comp.get("label", "")
        voltage = comp.get("voltage")
        resistance = comp.get("resistance")
        length_cm = comp.get("length_cm")

        if ctype == "battery":
            txt = f"{label_text} {voltage}V" if voltage else (label_text or "Battery")
            return elm.Battery().label(txt)

        elif ctype == "cell":
            txt = f"{label_text} {voltage}V" if voltage else (label_text or "Cell")
            return elm.BatteryCell().label(txt)

        elif ctype == "switch":
            return elm.Switch().label(label_text or "SW")

        elif ctype == "key":
            return elm.Switch().label(label_text or "K")

        elif ctype == "bulb":
            return elm.Lamp().label(label_text or "L")

        elif ctype == "resistor":
            txt = f"{label_text} {resistance}" + chr(937) if resistance else (label_text or "R")
            return elm.Resistor().label(txt)

        elif ctype == "variable_resistor":
            return elm.ResistorVar().label(label_text or "Rvar")

        elif ctype == "unknown_resistor":
            return elm.Box().label(label_text or "X")

        elif ctype == "ammeter":
            return elm.MeterA().label(label_text or "A")

        elif ctype == "voltmeter":
            return elm.MeterV().label(label_text or "V")

        elif ctype == "galvanometer":
            return elm.MeterAnalog().label(label_text or "G")

        elif ctype == "potentiometer":
            return elm.Potentiometer().label(label_text or "Pot")

        elif ctype == "wire":
            wire_label = label_text or (f"{length_cm}cm" if length_cm else "")
            return elm.Line().label(wire_label) if wire_label else elm.Line()

        elif ctype in ("capacitor", "inductor", "ac_source"):
            return elm.Line()

        return elm.Line()

    # ==========================================================
    # Series drawing
    # ==========================================================

    def _draw_series(self, blueprint: Dict) -> schemdraw.Drawing:
        d = schemdraw.Drawing()
        comps = blueprint.get("components", [])
        count = len(comps)

        for comp in comps:
            d += self._make_element(comp)

        d += elm.Line().down()
        d += elm.Line().left(d.unit * count)
        d += elm.Line().up()

        return d

    # ==========================================================
    # Parallel drawing
    # ==========================================================

    def _draw_parallel(self, blueprint: Dict) -> schemdraw.Drawing:
        d = schemdraw.Drawing()
        comps = blueprint.get("components", [])

        # Source (battery/cell) first, then branches
        ordered: list = []
        for comp in comps:
            if comp.get("type") in ("battery", "cell"):
                ordered.insert(0, comp)
            else:
                ordered.append(comp)

        if not ordered:
            return d

        d += self._make_element(ordered[0])
        d.push()

        for comp in ordered[1:]:
            d.push()
            d += elm.Line().right()
            d += self._make_element(comp)
            d += elm.Line().left()
            d.pop()

        return d

    # ==========================================================
    # Wheatstone bridge drawing
    # ==========================================================

    def _draw_bridge(self, blueprint: Dict) -> schemdraw.Drawing:
        d = schemdraw.Drawing()
        comps = blueprint.get("components", [])
        lookup = {c["id"]: c for c in comps}

        batt = None
        galv = None
        rest = []
        for c in comps:
            if c["type"] in ("battery", "cell"):
                batt = c
            elif c["type"] == "galvanometer":
                galv = c
            else:
                rest.append(c)

        rmap = {r["id"]: r for r in rest}

        p = rmap.get("P", rest[0] if len(rest) > 0 else None)
        q = rmap.get("Q", rest[1] if len(rest) > 1 else None)
        r = rmap.get("R", rest[2] if len(rest) > 2 else None)
        s = rmap.get("S", rest[3] if len(rest) > 3 else None)

        d += self._make_element(p).right().label("P")
        d += self._make_element(q).down().label("Q")

        d.push()
        if r:
            d += self._make_element(r).up().label("R")
        d.pop()

        if s:
            d += self._make_element(s).left().label("S")

        if galv:
            d += self._make_element(galv)

        if batt:
            d += self._make_element(batt)

        return d

    # ==========================================================
    # Meter bridge drawing
    # ==========================================================

    def _draw_meter_bridge(self, blueprint: Dict) -> schemdraw.Drawing:
        d = schemdraw.Drawing()
        comps = blueprint.get("components", [])

        drawn_wire = False
        for comp in comps:
            if comp.get("type") == "wire" and not drawn_wire:
                lbl = comp.get("label", "")
                length = comp.get("length_cm", "")
                label_text = lbl or (f"{length} cm" if length else "")
                if label_text:
                    d += elm.Line().right(8).label(label_text)
                else:
                    d += elm.Line().right(8)
                drawn_wire = True
                break

        if not drawn_wire:
            d += elm.Line().right(6).label("Meter Wire")

        return d

    # ==========================================================
    # File output
    # ==========================================================

    def render_to_file(
        self,
        blueprint: Dict,
        layout: Dict,
        solution: Dict,
        output_path: str
    ) -> str:
        drawing = self.render(blueprint, layout, solution)
        drawing.save(output_path)
        return output_path


if __name__ == "__main__":
    import json

    from circuit_topology import CircuitTopology
    from circuit_layout import CircuitLayout
    from circuit_solver import CircuitSolver

    with open("circuit_blueprints.json", "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    topologist = CircuitTopology()
    layout_engine = CircuitLayout()
    solver = CircuitSolver()
    renderer = CircuitRenderer()

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    print("=" * 64)
    print("  CIRCUIT RENDER TEST")
    print("=" * 64)

    all_ok = True
    for bp in blueprints:
        qid = bp.get("question_id", "?")
        try:
            topology = topologist.build(bp)
            layout = layout_engine.generate(topology, bp)
            solution = solver.solve(bp, topology)
            file_path = output_dir / f"{qid}.svg"
            renderer.render_to_file(bp, layout, solution, str(file_path))
            print(f"  {qid} -> {file_path}")
        except Exception as e:
            print(f"  {qid} FAILED: {e}")
            all_ok = False

    print(f"\n{'=' * 64}")
    print(f"  RENDER {'COMPLETE' if all_ok else 'FAILURES DETECTED'}")
    print(f"{'=' * 64}")
