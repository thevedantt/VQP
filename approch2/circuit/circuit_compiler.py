"""
circuit_compiler.py

Schema V2 compiler.
Orchestrates: validate -> topology -> layout -> solver -> renderer -> SVG.
No Schemdraw dependency. Uses custom SVG component library.
"""

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

        svg_markup = self.renderer.render(blueprint, layout, solution)

        return {
            "status": "SUCCESS",
            "stage": "complete",
            "blueprint_id": blueprint.get("question_id", "unknown"),
            "circuit_type": blueprint.get("circuit_type", "?"),
            "validation": validation,
            "topology": topology,
            "layout": layout,
            "solution": solution,
            "svg_markup": svg_markup
        }

    def compile_to_svg(
        self,
        blueprint: Dict,
        output_path: Optional[str] = None
    ) -> Dict:
        result = self.compile(blueprint)

        if result["status"] == "FAILED":
            return result

        if output_path is None:
            output_path = f"{result['blueprint_id']}.svg"

        Path(output_path).write_text(result["svg_markup"], encoding="utf-8")
        result["output_file"] = output_path
        del result["svg_markup"]

        return result


if __name__ == "__main__":
    import sys

    blueprint_file = sys.argv[1] if len(sys.argv) > 1 else "circuit_blueprints.json"

    with open(blueprint_file, "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    compiler = CircuitCompiler()
    output_dir = Path("opcompos")
    output_dir.mkdir(exist_ok=True)

    print("=" * 64)
    print("  CIRCUIT COMPILER REPORT (CUSTOM SVG)")
    print("=" * 64)

    results = []
    for bp in blueprints:
        qid = bp.get("question_id", "?")
        ctype = bp.get("circuit_type", "?")
        safe_ctype = ctype.replace("_", "_")
        out_path = str(output_dir / f"{qid}_{ctype}.svg")

        result = compiler.compile_to_svg(bp, out_path)
        results.append(result)

        status = result["status"]
        print(f"\n  {qid} ({ctype}): {status}")

        if status == "FAILED":
            for err in result.get("errors", []):
                print(f"    ERROR: {err}")
            continue

        topo = result["topology"]
        soln = result["solution"]
        print(f"    Nodes: {topo['node_count']}, Components: {topo['component_count']}")
        print(f"    Layout: {result['layout']['layout_type']}")
        print(f"    Solution: {soln.get('circuit_mode', '?')}")
        if soln.get("message"):
            print(f"    Info: {soln['message']}")
        print(f"    Output: {result['output_file']}")

    passed = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] == "FAILED")

    print(f"\n{'=' * 64}")
    print(f"  COMPILATION COMPLETE: {passed} passed, {failed} failed")
    print(f"{'=' * 64}")
