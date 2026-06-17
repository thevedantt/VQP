from pathlib import Path
from typing import Dict

import schemdraw
import schemdraw.elements as elm


class CircuitRenderer:

    def render(self, blueprint: Dict, layout: Dict, solution: Dict) -> schemdraw.Drawing:
        circuit_type = blueprint["circuit_type"]

        if circuit_type in {
            "simple_series", "series_resistors", "three_resistor_series",
            "ammeter_series", "cell_key_bulb"
        }:
            return self._render_series(blueprint, layout, solution)

        elif circuit_type in {
            "parallel_resistors", "three_parallel", "voltmeter_parallel"
        }:
            return self._render_parallel(blueprint, layout, solution)

        elif circuit_type == "wheatstone_bridge":
            return self._render_bridge(blueprint, layout, solution)

        elif circuit_type == "meter_bridge":
            return self._render_meter_bridge(blueprint, layout, solution)

        raise ValueError(f"Unsupported circuit type: {circuit_type}")

    # --------------------------------------------------
    # Series rendering
    # --------------------------------------------------

    def _render_series(self, blueprint, layout, solution):
        d = schemdraw.Drawing()
        comps = blueprint["components"]

        for i, comp in enumerate(comps):
            ctype = comp["type"]
            self._add_element(d, comp, i == len(comps) - 1)

        self._close_series(d, len(comps))
        return d

    def _close_series(self, d, count):
        d += elm.Line().down()
        d += elm.Line().left(d.unit * count)
        d += elm.Line().up()

    # --------------------------------------------------
    # Parallel rendering
    # --------------------------------------------------

    def _render_parallel(self, blueprint, layout, solution):
        d = schemdraw.Drawing()
        comps = blueprint["components"]
        branches = []

        for comp in comps:
            ctype = comp["type"]
            if ctype in ("battery", "cell"):
                branches.insert(0, comp)
            else:
                branches.append(comp)

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
    # Wheatstone bridge
    # --------------------------------------------------

    def _render_bridge(self, blueprint, layout, solution):
        d = schemdraw.Drawing()
        comps = blueprint["components"]
        lookup = {c["id"]: c for c in comps}

        r1 = lookup.get("R1")
        r2 = lookup.get("R2")
        r3 = lookup.get("R3")
        r4 = lookup.get("R4")
        g1 = lookup.get("G1")

        d += self._make_element(r1).right().label("P")
        d += self._make_element(r2).down().label("Q")

        d.push()
        d += self._make_element(r3).up().label("R")
        d.pop()

        d += self._make_element(r4).left().label("S")

        return d

    # --------------------------------------------------
    # Meter bridge
    # --------------------------------------------------

    def _render_meter_bridge(self, blueprint, layout, solution):
        d = schemdraw.Drawing()
        comps = blueprint["components"]

        for comp in comps:
            ctype = comp["type"]
            if ctype == "wire":
                d += elm.Line().right(6).label(comp.get("metadata", {}).get("label", ""))
                break

        return d

    # --------------------------------------------------
    # Element factory
    # --------------------------------------------------

    def _make_element(self, comp):
        ctype = comp["type"]
        label = comp.get("metadata", {}).get("label", "")
        value = comp.get("value")

        if ctype == "battery":
            el = elm.Battery().label(f"{label} {value}V" if value else label)
        elif ctype == "cell":
            el = elm.BatteryCell().label(f"{label} {value}V" if value else label)
        elif ctype == "key":
            el = elm.Switch().label(label)
        elif ctype == "bulb":
            el = elm.Lamp().label(label)
        elif ctype == "resistor":
            el = elm.Resistor().label(f"{label} {value}\u03a9" if value else label)
        elif ctype == "unknown_resistor":
            el = elm.Box().label(label)
        elif ctype == "ammeter":
            el = elm.MeterA().label(label)
        elif ctype == "voltmeter":
            el = elm.MeterV().label(label)
        elif ctype == "galvanometer":
            el = elm.MeterAnalog().label(label)
        else:
            el = elm.Line()
        return el

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
            print(bp["question_id"], "->", file_path)

        except Exception as e:
            print(bp["question_id"], "FAILED:", e)
