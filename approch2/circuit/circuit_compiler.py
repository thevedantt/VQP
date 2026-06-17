"""
circuit_compiler.py

Final orchestration layer.
Pipeline: validate -> topology -> layout -> solver -> renderer -> SVG.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

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
                "valid": False,
                "errors": validation["errors"],
                "topology": None,
                "layout": None,
                "solution": None,
                "svg": None,
            }

        try:
            topology = self.topologist.build(blueprint)
            layout = self.layout_engine.generate(topology, blueprint)
            solution = self.solver.solve(blueprint, topology)
            svg = self.renderer.render(blueprint, layout, solution)

            return {
                "valid": True,
                "errors": [],
                "topology": topology,
                "layout": layout,
                "solution": solution,
                "svg": svg,
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "topology": None,
                "layout": None,
                "solution": None,
                "svg": None,
            }

    def compile_to_file(self, blueprint: Dict, output_file: str) -> Dict:
        result = self.compile(blueprint)

        if not result["valid"]:
            return {
                "success": False,
                "errors": result["errors"],
                "output_file": None,
            }

        svg = result["svg"]
        Path(output_file).write_text(svg, encoding="utf-8")

        return {
            "success": True,
            "errors": [],
            "output_file": output_file,
        }

    def compile_many(self, blueprints: List[Dict]) -> List[Dict]:
        return [self.compile(bp) for bp in blueprints]


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    blueprint_path = script_dir / "circuit_blueprints.json"
    with open(str(blueprint_path), "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    compiler = CircuitCompiler()
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)

    print("CIRCUIT COMPILER REPORT")
    print("=" * 66)

    all_results = []

    for bp in blueprints:
        qid = bp.get("question_id", "???")

        out_path = str(output_dir / f"{qid}.svg")
        comp_result = compiler.compile_to_file(bp, out_path)
        all_results.append(comp_result)

        print()
        print("=" * 66)
        print(f"  {qid}")
        print(f"  VALID : {comp_result['success']}")
        if comp_result["success"]:
            print(f"  SVG   : {comp_result['output_file']}")
        else:
            for err in comp_result.get("errors", []):
                print(f"  ERROR : {err}")

    success_count = sum(1 for r in all_results if r["success"])
    fail_count = sum(1 for r in all_results if not r["success"])

    print()
    print("=" * 66)
    print(f"  COMPILED: {success_count} OK, {fail_count} FAILED")
    print("=" * 66)
