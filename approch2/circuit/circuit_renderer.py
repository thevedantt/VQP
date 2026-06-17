"""
circuit_renderer.py

Custom SVG-based renderer.
Uses SVG primitives + circuit component library instead of Schemdraw.

Responsibility: layout + solution → SVG markup.
Does NOT calculate physics, does NOT validate, does NOT build topology.
"""

from pathlib import Path
from typing import Dict, Optional

from svg.svg_canvas import SVGCanvas
from svg.svg_line import SVGLine
from svg.svg_circle import SVGCircle
from svg.svg_text import SVGText

from components.wire import Wire
from components.resistor import Resistor
from components.battery import Battery
from components.cell import Cell
from components.bulb import Bulb
from components.switch import Switch
from components.ammeter import Ammeter
from components.voltmeter import Voltmeter
from components.galvanometer import Galvanometer
from components.potentiometer import Potentiometer

from circuit_rules import SERIES_CIRCUITS, PARALLEL_CIRCUITS


class CircuitRenderer:

    NODE_DOT_R = 3

    COMPONENT_FACTORY = {
        "battery": Battery(),
        "cell": Cell(),
        "resistor": Resistor(),
        "variable_resistor": Resistor(),
        "unknown_resistor": Resistor(),
        "bulb": Bulb(),
        "switch": Switch(),
        "key": Switch(),
        "ammeter": Ammeter(),
        "voltmeter": Voltmeter(),
        "galvanometer": Galvanometer(),
        "potentiometer": Potentiometer(),
        "wire": Wire()
    }

    MARGIN = 40

    def render(self, blueprint: Dict, layout: Dict, solution: Dict) -> str:
        canvas = SVGCanvas()

        net_positions = layout.get("net_positions", {})
        placements = layout.get("component_placements", {})
        components = blueprint.get("components", [])
        solution_data = solution or {}
        bounds = layout.get("bounds", {})

        if bounds:
            min_x = bounds.get("min_x", 0) - self.MARGIN
            min_y = bounds.get("min_y", 0) - self.MARGIN
            w = bounds.get("width", 400) + self.MARGIN * 2
            h = bounds.get("height", 300) + self.MARGIN * 2
            canvas.width = w
            canvas.height = h
            canvas.viewbox = f"{min_x} {min_y} {w} {h}"

        self._draw_nodes(canvas, net_positions)
        self._draw_interconnects(canvas, net_positions, components)
        self._draw_components(canvas, components, placements, solution_data)

        return canvas.render()

    # --------------------------------------------------
    # Node dots
    # --------------------------------------------------

    def _draw_nodes(self, canvas: SVGCanvas, net_positions: Dict) -> None:
        r = self.NODE_DOT_R
        for nid, pos in net_positions.items():
            canvas.add_markup(SVGCircle(pos["x"], pos["y"], r, fill="black").render())

    # --------------------------------------------------
    # Wires between nodes
    # --------------------------------------------------

    def _draw_interconnects(
        self,
        canvas: SVGCanvas,
        net_positions: Dict,
        components: list
    ) -> None:
        drawn_pairs = set()

        for comp in components:
            cfrom = comp.get("from", "")
            cto = comp.get("to", "")
            if not cfrom or not cto:
                continue

            pair = frozenset([cfrom, cto])
            if pair in drawn_pairs:
                continue
            drawn_pairs.add(pair)

            p1 = net_positions.get(cfrom)
            p2 = net_positions.get(cto)
            if p1 and p2:
                canvas.add_markup(SVGLine(p1["x"], p1["y"], p2["x"], p2["y"]).render())

    # --------------------------------------------------
    # Component symbols
    # --------------------------------------------------

    def _draw_components(
        self,
        canvas: SVGCanvas,
        components: list,
        placements: Dict,
        solution: Dict
    ) -> None:
        for comp in components:
            cid = comp.get("id", "")
            ctype = comp.get("type", "")
            placement = placements.get(cid)

            if not placement:
                continue

            px = placement.get("x", 0)
            py = placement.get("y", 0)
            rotation = placement.get("angle", 0)

            component = self.COMPONENT_FACTORY.get(ctype)
            if component is None:
                continue

            label = comp.get("label", "")

            value_text = self._get_value_text(comp, solution, cid)

            state = comp.get("state", "closed")

            markup = component.render(
                x=px, y=py,
                rotation=rotation,
                label=label or None,
                value=value_text,
                voltage=comp.get("voltage"),
                state=state
            )
            canvas.add_markup(markup)

    def _get_value_text(self, comp: Dict, solution: Dict, cid: str) -> Optional[str]:
        ctype = comp.get("type", "")
        if ctype == "resistor":
            val = comp.get("resistance")
            if val is not None:
                return str(val)
        elif ctype in ("battery", "cell"):
            val = comp.get("voltage")
            if val is not None:
                return str(val)

        return None

    # --------------------------------------------------
    # File output
    # --------------------------------------------------

    def render_to_file(
        self,
        blueprint: Dict,
        layout: Dict,
        solution: Dict,
        output_path: str
    ) -> str:
        svg_markup = self.render(blueprint, layout, solution)
        Path(output_path).write_text(svg_markup, encoding="utf-8")
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
    print("  CIRCUIT RENDER TEST (CUSTOM SVG)")
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
