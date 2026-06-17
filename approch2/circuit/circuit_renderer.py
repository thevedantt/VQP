from pathlib import Path
from typing import Dict

import schemdraw
import schemdraw.elements as elm

from circuit_rules import SERIES_CIRCUITS, PARALLEL_CIRCUITS


class CircuitRenderer:

    def render(self, blueprint: Dict, layout: Dict, solution: Dict) -> schemdraw.Drawing:
        circuit_type = blueprint["circuit_type"]

        if circuit_type in SERIES_CIRCUITS:
            return self._render_series(blueprint, layout, solution)
        elif circuit_type in PARALLEL_CIRCUITS:
            return self._render_parallel(blueprint, layout, solution)
        elif circuit_type == "wheatstone_bridge":
            return self._render_bridge(blueprint, layout, solution)
        elif circuit_type == "meter_bridge":
            return self._render_meter_bridge(blueprint, layout, solution)
        else:
            raise ValueError(f"Unsupported circuit type: {circuit_type}")

    # --------------------------------------------------
    # Series
    # --------------------------------------------------

    def _render_series(self, blueprint, layout, solution):
        d = schemdraw.Drawing()
        comps = blueprint["components"]
        count = len(comps)

        for i, comp in enumerate(comps):
            self._add_element(
                d, comp,
                is_last=(i == count - 1)
            )

        d += elm.Line().down()
        d += elm.Line().left(d.unit * count)
        d += elm.Line().up()
        return d

    # --------------------------------------------------
    # Parallel
    # --------------------------------------------------

    def _render_parallel(self, blueprint, layout, solution):
        d = schemdraw.Drawing()
        comps = blueprint["components"]

        branches = []
        for comp in comps:
            if comp["type"] in ("battery", "cell"):
                branches.insert(0, comp)
            else:
                branches.append(comp)

        if not branches:
            return d

        d += self._make_element(branches[0])
        d.push()

        for comp in branches[1:]:
            d.push()
            d += elm.Line().right()
            d += self._make_element(comp)
            d += elm.Line().left()
            d.pop()

        return d

    # --------------------------------------------------
    # Wheatstone Bridge
    # --------------------------------------------------

    def _render_bridge(self, blueprint, layout, solution):
        d = schemdraw.Drawing()
        comps = blueprint["components"]
        lookup = {c["id"]: c for c in comps}

        battery = None
        resistors = []
        galvanometer = None

        for c in comps:
            if c["type"] in ("battery", "cell"):
                battery = c
            elif c["type"] == "galvanometer":
                galvanometer = c
            else:
                resistors.append(c)

        resistor_map = {}
        for r in resistors:
            resistor_map[r["id"]] = r

        d += self._make_element(resistor_map.get("P", resistors[0] if resistors else None)).right().label("P")
        d += self._make_element(resistor_map.get("Q", resistors[1] if len(resistors) > 1 else None)).down().label("Q")

        d.push()
        r_res = resistor_map.get("R", resistors[2] if len(resistors) > 2 else None)
        if r_res:
            d += self._make_element(r_res).up().label("R")
        d.pop()

        s_res = resistor_map.get("S", resistors[3] if len(resistors) > 3 else None)
        if s_res:
            d += self._make_element(s_res).left().label("S")

        if galvanometer:
            d += self._make_element(galvanometer)

        if battery:
            d += self._make_element(battery)

        return d

    # --------------------------------------------------
    # Meter Bridge
    # --------------------------------------------------

    def _render_meter_bridge(self, blueprint, layout, solution):
        d = schemdraw.Drawing()
        comps = blueprint["components"]

        wire_found = False
        for comp in comps:
            if comp["type"] == "wire":
                if not wire_found:
                    label = comp.get("label", "")
                    d += elm.Line().right(8).label(label)
                    wire_found = True

        if not wire_found:
            d += elm.Line().right(6).label("Meter Wire")

        return d

    # --------------------------------------------------
    # Element factory
    # --------------------------------------------------

    def _make_element(self, comp):
        if comp is None:
            return elm.Line()

        ctype = comp["type"]
        label = comp.get("label", "")
        voltage = comp.get("voltage")
        resistance = comp.get("resistance")

        if ctype == "battery":
            txt = f"{label} {voltage}V" if voltage else (label or "Battery")
            return elm.Battery().label(txt)
        elif ctype == "cell":
            txt = f"{label} {voltage}V" if voltage else (label or "Cell")
            return elm.BatteryCell().label(txt)
        elif ctype in ("switch", "key"):
            return elm.Switch().label(label or ("K" if ctype == "key" else "SW"))
        elif ctype == "bulb":
            return elm.Lamp().label(label or "L")
        elif ctype == "resistor":
            txt = f"{label} {resistance}\u03a9" if resistance else (label or "R")
            return elm.Resistor().label(txt)
        elif ctype == "variable_resistor":
            return elm.ResistorVar().label(label)
        elif ctype == "unknown_resistor":
            return elm.Box().label(label or "X")
        elif ctype == "ammeter":
            return elm.MeterA().label(label or "A")
        elif ctype == "voltmeter":
            return elm.MeterV().label(label or "V")
        elif ctype == "galvanometer":
            return elm.MeterAnalog().label(label or "G")
        elif ctype in ("wire", "potentiometer"):
            return elm.Line()
        else:
            return elm.Line()

    def _add_element(self, d, comp, is_last=False):
        d += self._make_element(comp)

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    def render_to_file(self, blueprint, layout, solution, output_file):
        drawing = self.render(blueprint, layout, solution)
        drawing.save(output_file)
        return output_file


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

    print("\nCIRCUIT RENDER TEST\n")

    for bp in blueprints:
        try:
            topology = topologist.build(bp)
            layout = layout_engine.generate(topology, bp)
            solution = solver.solve(bp, topology)

            file_path = output_dir / f"{bp['question_id']}.svg"
            renderer.render_to_file(bp, layout, solution, str(file_path))
            print(f"{bp['question_id']} -> {file_path}")

        except Exception as e:
            print(f"{bp['question_id']} FAILED: {e}")
