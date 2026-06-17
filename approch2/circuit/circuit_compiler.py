import json
from pathlib import Path
from typing import Dict, Optional

from circuit_validation import CircuitValidation
from circuit_topology import CircuitTopology
from circuit_layout import CircuitLayout
from circuit_solver import CircuitSolver
from circuit_renderer import CircuitRenderer


class CircuitCompiler:

    def __init__(self):
        self.validator = CircuitValidation()
        self.topologist = CircuitTopology()
        self.layout_engine = CircuitLayout()
        self.solver = CircuitSolver()
        self.renderer = CircuitRenderer()

    def compile(self, blueprint: Dict) -> Dict:
        validation = self.validator.validate(blueprint)
        if not validation["valid"]:
            return {
                "status": "FAILED",
                "stage": "validation",
                "errors": validation["errors"],
                "blueprint_id": blueprint.get("question_id", "unknown")
            }

        topology = self.topologist.build(blueprint)
        layout = self.layout_engine.generate(topology, blueprint)
        solution = self.solver.solve(blueprint, topology)
        drawing = self.renderer.render(blueprint, layout, solution)

        return {
            "status": "SUCCESS",
            "stage": "complete",
            "blueprint_id": blueprint.get("question_id", "unknown"),
            "validation": validation,
            "topology": topology,
            "layout": layout,
            "solution": solution,
            "drawing": drawing
        }

    def compile_to_svg(self, blueprint: Dict, output_path: Optional[str] = None) -> Dict:
        result = self.compile(blueprint)

        if result["status"] == "FAILED":
            return result

        if output_path is None:
            output_path = f"{result['blueprint_id']}.svg"

        result["drawing"].save(output_path)
        result["output_file"] = output_path

        return result


if __name__ == "__main__":
    import sys

    blueprint_file = sys.argv[1] if len(sys.argv) > 1 else "circuit_blueprints.json"

    with open(blueprint_file, "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    compiler = CircuitCompiler()

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    print("\nCIRCUIT COMPILER REPORT\n")

    for bp in blueprints:
        print("=" * 60)
        qid = bp.get("question_id", "?")

        result = compiler.compile_to_svg(
            bp,
            str(output_dir / f"{qid}.svg")
        )

        print(f"{qid}: {result['status']}")

        if result["status"] == "FAILED":
            for err in result.get("errors", []):
                print(f"  ERROR: {err}")
            continue

        topo = result["topology"]
        soln = result["solution"]
        print(f"  Nodes: {topo['node_count']}, Components: {topo['component_count']}")
        print(f"  Layout: {result['layout']['layout_type']}")
        print(f"  Solution mode: {soln.get('circuit_mode', '?')}")
        print(f"  Output: {result['output_file']}")

    print("\n" + "=" * 60)
    print("COMPILATION COMPLETE")
