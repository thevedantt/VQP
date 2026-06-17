from pathlib import Path
from typing import Dict, Optional
from math import atan2, degrees

import schemdraw
import schemdraw.elements as elm


class CircuitRenderer:

    def render(self, blueprint: Dict, layout: Dict, solution: Dict) -> str:
        circuit_type = blueprint.get("circuit_type", "")
        comp_list = blueprint.get("components", [])
        comp_map = {c["id"]: c for c in comp_list}

        dispatch = {
            "series": self._render_series,
            "ammeter_series": self._render_series,
            "parallel": self._render_parallel,
            "voltmeter_parallel": self._render_voltmeter_parallel,
            "wheatstone_bridge": self._render_wheatstone_bridge,
            "meter_bridge": self._render_meter_bridge,
            "potentiometer": self._render_potentiometer,
        }

        render_fn = dispatch.get(circuit_type)
        if render_fn is None:
            raise ValueError(f"No schemdraw renderer for '{circuit_type}'")

        comp_vals = {}
        for c in comp_list:
            v = self._component_value(c)
            if v:
                comp_vals[c["id"]] = v

        d = render_fn(comp_map, comp_vals, blueprint)
        return d._repr_svg_()

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def _component_value(self, comp: Dict) -> Optional[str]:
        ctype = comp.get("type", "")
        if ctype == "resistor":
            v = comp.get("resistance")
            return f"{v}\u03A9" if v is not None else None
        if ctype == "unknown_resistor":
            return "?"
        if ctype == "bulb":
            v = comp.get("resistance")
            return f"{v}\u03A9" if v is not None else None
        if ctype in ("battery", "cell"):
            v = comp.get("voltage")
            return f"{v}V" if v is not None else None
        return None

    def _theta(self, x1, y1, x2, y2):
        return degrees(atan2(y2 - y1, x2 - x1))

    def _mid(self, x1, y1, x2, y2):
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def _dot(self, d, x, y, r=0.08):
        d += elm.Dot(radius=r).at((x, y))

    def _wire(self, d, x1, y1, x2, y2):
        if x1 == x2 and y1 == y2:
            return
        d += elm.Line().at((x1, y1)).to((x2, y2))

    def _resistor(self, d, x1, y1, x2, y2, label="", reverse=False):
        el = elm.Resistor().at((x1, y1)).to((x2, y2))
        if reverse:
            el = el.reverse()
        if label:
            el = el.label(label)
        d += el

    def _battery(self, d, x1, y1, x2, y2, label="", cell=False):
        el = (elm.BatteryCell() if cell else elm.Battery()).at((x1, y1)).to((x2, y2))
        if label:
            el = el.label(label)
        d += el

    def _switch(self, d, x1, y1, x2, y2, label="", state="closed"):
        if state == "open":
            d += elm.Line().at((x1, y1)).to((x2, y2))
            return
        el = elm.Switch().at((x1, y1)).to((x2, y2))
        if label:
            el = el.label(label)
        d += el

    def _lamp(self, d, x1, y1, x2, y2, label=""):
        el = elm.Lamp().at((x1, y1)).to((x2, y2))
        if label:
            el = el.label(label)
        d += el

    def _meter(self, d, x1, y1, x2, y2, meter_type="A", label=""):
        el_map = {"A": elm.MeterA, "V": elm.MeterV, "G": elm.MeterAnalog}
        cls = el_map.get(meter_type, elm.MeterAnalog)
        el = cls().at((x1, y1)).to((x2, y2))
        if label:
            el = el.label(label)
        d += el

    def _jockey(self, d, x, y, direction="down", size=0.5):
        if direction == "down":
            d += elm.Arrow().at((x, y)).down().length(size)
        else:
            d += elm.Arrow().at((x, y)).up().length(size)

    # ----------------------------------------------------------
    # SERIES (C1, C2, C3, C6, C8)
    # ----------------------------------------------------------

    def _render_series(self, comp_map, comp_vals, blueprint):
        d = schemdraw.Drawing()
        components = blueprint.get("components", [])
        u = 2.0
        n = len(components)
        total_w = (n + 1) * u
        y = 0.0

        node_x = [i * u for i in range(n + 1)]

        for i in range(n + 1):
            self._dot(d, node_x[i], y)

        for i, comp in enumerate(components):
            cid = comp["id"]
            ctype = comp["type"]
            val = comp_vals.get(cid, "")
            x1, x2 = node_x[i], node_x[i + 1]
            if ctype in ("battery",):
                self._battery(d, x1, y, x2, y, val)
            elif ctype in ("cell",):
                self._battery(d, x1, y, x2, y, val, cell=True)
            elif ctype == "resistor":
                self._resistor(d, x1, y, x2, y, val)
            elif ctype == "unknown_resistor":
                self._resistor(d, x1, y, x2, y, "?")
            elif ctype == "bulb":
                self._lamp(d, x1, y, x2, y, val)
            elif ctype in ("switch", "key"):
                state = comp.get("state", "closed")
                lbl = "SW" if ctype == "switch" else "K"
                self._switch(d, x1, y, x2, y, lbl, state)
            elif ctype == "ammeter":
                d += elm.MeterA().at((x1, y)).to((x2, y)).label("A")
            elif ctype == "voltmeter":
                d += elm.MeterV().at((x1, y)).to((x2, y)).label("V")
            elif ctype == "galvanometer":
                d += elm.MeterAnalog().at((x1, y)).to((x2, y)).label("G")
            else:
                d += elm.Line().at((x1, y)).to((x2, y))

        bot_y = y - u
        self._wire(d, node_x[n], y, node_x[n], bot_y)
        self._wire(d, node_x[n], bot_y, node_x[0], bot_y)
        self._wire(d, node_x[0], bot_y, node_x[0], y)

        return d

    # ----------------------------------------------------------
    # PARALLEL (C4, C5)
    # ----------------------------------------------------------

    def _render_parallel(self, comp_map, comp_vals, blueprint):
        d = schemdraw.Drawing()
        components = blueprint.get("components", [])
        u = 2.0

        branch_ids = []
        source_id = None
        for c in components:
            if c["type"] in ("battery", "cell"):
                source_id = c["id"]
            else:
                branch_ids.append(c["id"])

        source = comp_map.get(source_id, {})
        source_type = source.get("type", "battery")
        source_label = comp_vals.get(source_id, "")
        n = len(branch_ids)

        top_y = u
        bot_y = -u
        start_x = 0.0
        spacing = 3.0

        for i, cid in enumerate(branch_ids):
            cx = start_x + i * spacing
            ctype = comp_map[cid]["type"]
            val = comp_vals.get(cid, "")

            self._dot(d, cx, top_y)
            self._dot(d, cx, bot_y)

            if ctype == "resistor":
                self._resistor(d, cx, top_y, cx, bot_y, val)
            elif ctype == "bulb":
                self._lamp(d, cx, top_y, cx, bot_y, val)
            elif ctype == "voltmeter":
                d += elm.MeterV().at((cx, top_y)).to((cx, bot_y)).label("V")
            elif ctype == "ammeter":
                d += elm.MeterA().at((cx, top_y)).to((cx, bot_y)).label("A")
            elif ctype == "galvanometer":
                d += elm.MeterAnalog().at((cx, top_y)).to((cx, bot_y)).label("G")
            else:
                self._wire(d, cx, top_y, cx, bot_y)

            if i > 0:
                prev_cx = start_x + (i - 1) * spacing
                self._wire(d, prev_cx, top_y, cx, top_y)
                self._wire(d, prev_cx, bot_y, cx, bot_y)

        src_x = start_x - spacing
        self._wire(d, src_x, top_y, start_x, top_y)
        self._wire(d, src_x, bot_y, start_x, bot_y)
        if source_type in ("battery",):
            self._battery(d, src_x, top_y, src_x, bot_y, source_label)
        else:
            self._battery(d, src_x, top_y, src_x, bot_y, source_label, cell=True)

        return d

    # ----------------------------------------------------------
    # VOLTMETER PARALLEL (C7)
    # ----------------------------------------------------------

    def _render_voltmeter_parallel(self, comp_map, comp_vals, blueprint):
        d = schemdraw.Drawing()
        u = 2.0

        bat_id = None
        res_id = None
        volt_id = None
        for cid, comp in comp_map.items():
            if comp["type"] in ("battery", "cell"):
                bat_id = cid
            elif comp["type"] == "resistor":
                res_id = cid
            elif comp["type"] == "voltmeter":
                volt_id = cid

        bat_val = comp_vals.get(bat_id, "")
        res_val = comp_vals.get(res_id, "")

        top_y = u
        bot_y = -u
        bat_top = (0, top_y)
        bat_bot = (0, bot_y)

        if comp_map.get(bat_id, {}).get("type") == "cell":
            self._battery(d, bat_top[0], bat_top[1], bat_bot[0], bat_bot[1], bat_val, cell=True)
        else:
            self._battery(d, bat_top[0], bat_top[1], bat_bot[0], bat_bot[1], bat_val)

        self._dot(d, bat_top[0], bat_top[1])
        self._dot(d, bat_bot[0], bat_bot[1])

        r_x = 2 * u
        self._wire(d, bat_top[0], bat_top[1], r_x, bat_top[1])
        self._dot(d, r_x, bat_top[1])
        self._resistor(d, r_x, bat_top[1], r_x, bat_bot[1], res_val)
        self._dot(d, r_x, bat_bot[1])
        self._wire(d, r_x, bat_bot[1], bat_bot[0], bat_bot[1])

        v_x = 4 * u
        self._wire(d, bat_top[0], bat_top[1], v_x, bat_top[1])
        self._dot(d, v_x, bat_top[1])
        d += elm.MeterV().at((v_x, bat_top[1])).to((v_x, bat_bot[1])).label("V")
        self._dot(d, v_x, bat_bot[1])
        self._wire(d, v_x, bat_bot[1], bat_bot[0], bat_bot[1])

        return d

    # ----------------------------------------------------------
    # WHEATSTONE BRIDGE (C9)
    # ----------------------------------------------------------

    def _render_wheatstone_bridge(self, comp_map, comp_vals, blueprint):
        d = schemdraw.Drawing()
        u = 2.0
        s = 2.0 * u

        A = (0, s)
        B = (-s, 0)
        C = (s, 0)
        D = (0, -s)

        for pt in [A, B, C, D]:
            self._dot(d, pt[0], pt[1])

        self._resistor(d, A[0], A[1], B[0], B[1], comp_vals.get("P", ""))
        self._resistor(d, B[0], B[1], D[0], D[1], comp_vals.get("Q", ""))
        self._resistor(d, A[0], A[1], C[0], C[1], comp_vals.get("R", ""))
        self._resistor(d, C[0], C[1], D[0], D[1], comp_vals.get("S", ""))

        self._wire(d, B[0], B[1], C[0], C[1])
        gx1, gy1 = self._mid(B[0], B[1], C[0], C[1])
        d += elm.MeterAnalog().at((gx1, gy1)).theta(0).label("G")

        bat_x = -s - u
        self._wire(d, A[0], A[1], bat_x, A[1])
        self._wire(d, bat_x, D[1], D[0], D[1])
        self._battery(d, bat_x, A[1], bat_x, D[1], comp_vals.get("BAT1", ""))

        return d

    # ----------------------------------------------------------
    # METER BRIDGE (C10)
    # ----------------------------------------------------------

    def _render_meter_bridge(self, comp_map, comp_vals, blueprint):
        d = schemdraw.Drawing()
        u = 2.0
        w = 6.0 * u

        A = (0.0, 0.0)
        J = (w / 2.0, 0.0)
        C = (w, 0.0)
        B = (w / 2.0, -3.0 * u)
        bot_y = -4.5 * u

        self._wire(d, A[0], A[1], J[0], J[1])
        self._wire(d, J[0], J[1], C[0], C[1])
        d += elm.Label().at((w / 2.0, 0.6)).label("100 cm bridge wire")

        self._resistor(d, A[0], A[1], B[0], B[1], comp_vals.get("R", ""))
        self._resistor(d, B[0], B[1], C[0], C[1], comp_vals.get("X", "?"))

        self._wire(d, B[0], B[1], J[0], J[1])
        mid_g = self._mid(B[0], B[1], J[0], J[1])
        d += elm.MeterAnalog().at(mid_g).theta(90).label("G")

        self._wire(d, A[0], A[1], A[0], bot_y)
        cell_val = comp_vals.get("CELL1", "")
        cell_type = comp_map.get("CELL1", {}).get("type", "cell")
        cell_w = 1.5 * u
        if cell_type == "cell":
            self._battery(d, A[0], bot_y, A[0] + cell_w, bot_y, cell_val, cell=True)
        else:
            self._battery(d, A[0], bot_y, A[0] + cell_w, bot_y, cell_val)

        kx1 = A[0] + cell_w + 0.3
        kx2 = kx1 + 1.5 * u
        self._switch(d, kx1, bot_y, kx2, bot_y, "K")

        self._wire(d, kx2, bot_y, C[0], bot_y)
        self._wire(d, C[0], bot_y, C[0], C[1])

        for pt in [A, J, C, B]:
            self._dot(d, pt[0], pt[1])

        self._jockey(d, J[0], J[1], "down", 0.8)
        d += elm.Label().at((J[0] + 0.4, J[1] - 0.3)).label("J")

        return d

    # ----------------------------------------------------------
    # POTENTIOMETER (C11)
    # ----------------------------------------------------------

    def _render_potentiometer(self, comp_map, comp_vals, blueprint):
        d = schemdraw.Drawing()
        u = 2.0
        w = 5.0 * u

        A = (0.0, 0.0)
        J = (w / 2.0, 0.0)
        C = (w, 0.0)
        pry = -2.5 * u
        sec_y = -4.5 * u
        B = (J[0], sec_y)

        self._wire(d, A[0], A[1], J[0], J[1])
        self._wire(d, J[0], J[1], C[0], C[1])

        self._wire(d, A[0], A[1], A[0], pry)
        cell_val = comp_vals.get("CELL1", "")
        cell_type = comp_map.get("CELL1", {}).get("type", "cell")
        cw = 1.5 * u
        if cell_type == "cell":
            self._battery(d, A[0], pry, A[0] + cw, pry, cell_val, cell=True)
        else:
            self._battery(d, A[0], pry, A[0] + cw, pry, cell_val)

        kx1 = A[0] + cw + 0.3
        kx2 = kx1 + 1.5 * u
        self._switch(d, kx1, pry, kx2, pry, "K")

        rx1 = kx2 + 0.3
        self._resistor(d, rx1, pry, C[0], pry, comp_vals.get("RH", ""))
        self._wire(d, C[0], pry, C[0], C[1])

        self._wire(d, J[0], J[1], B[0], B[1])
        mid_g = self._mid(J[0], J[1], B[0], B[1])
        d += elm.MeterAnalog().at(mid_g).theta(90).label("G")

        self._wire(d, B[0], B[1], A[0], B[1])
        cell2_val = comp_vals.get("CELL2", "")
        cell2_type = comp_map.get("CELL2", {}).get("type", "cell")
        if cell2_type == "cell":
            self._battery(d, A[0], B[1], A[0], A[1], cell2_val, cell=True)
        else:
            self._battery(d, A[0], B[1], A[0], A[1], cell2_val)

        d += elm.Label().at((A[0] - 0.3, A[1])).label("A")
        d += elm.Label().at((C[0] + 0.3, C[1])).label("C")
        d += elm.Label().at((B[0] + 0.4, B[1])).label("B")

        for pt in [A, J, C, B]:
            self._dot(d, pt[0], pt[1])

        self._jockey(d, J[0], J[1], "down", 0.8)
        d += elm.Label().at((J[0] + 0.4, J[1] - 0.3)).label("J")

        return d

    # ----------------------------------------------------------
    # File output
    # ----------------------------------------------------------

    def render_to_file(self, blueprint, layout, solution, output_path):
        svg_markup = self.render(blueprint, layout, solution)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_markup)
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
    print("  CIRCUIT RENDER TEST (SCHEMDRAW)")
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
            import traceback
            traceback.print_exc()
            all_ok = False

    print(f"\n{'=' * 64}")
    print(f"  RENDER {'COMPLETE' if all_ok else 'FAILURES DETECTED'}")
    print(f"{'=' * 64}")
