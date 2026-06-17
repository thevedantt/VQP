"""
circuit_compiler.py

Schema V2 compiler.
Responsibility: orchestrate the pipeline: validate → topology → layout → solver → renderer → SVG.
Does NOT perform any stage's work itself.
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

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def compile(self, blueprint: Dict) -> Dict:
        """
        Run the full pipeline on a single blueprint.
        Returns a result dict with all stage outputs.
        """
        # Stage 1: validation
        validation = self.validator.validate(blueprint)
        if not validation["valid"]:
            return {
                "status": "FAILED",
                "stage": "validation",
                "errors": validation["errors"],
                "blueprint_id": blueprint.get("question_id", "unknown")
            }

        # Stage 2: topology
        topology = self.topologist.build(blueprint)

        # Stage 3: layout
        layout = self.layout_engine.generate(topology, blueprint)

        # Stage 4: solver
        solution = self.solver.solve(blueprint, topology)

        # Stage 5: rendering (returns schemdraw Drawing object)
        drawing = self.renderer.render(blueprint, layout, solution)

        return {
            "status": "SUCCESS",
            "stage": "complete",
            "blueprint_id": blueprint.get("question_id", "unknown"),
            "circuit_type": blueprint.get("circuit_type", "?"),
            "validation": validation,
            "topology": topology,
            "layout": layout,
            "solution": solution,
            "drawing": drawing
        }

    def compile_to_svg(
        self,
        blueprint: Dict,
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Compile and save the result as SVG.
        """
        result = self.compile(blueprint)

        if result["status"] == "FAILED":
            return result

        if output_path is None:
            output_path = f"{result['blueprint_id']}.svg"

        result["drawing"].save(output_path)
        result["output_file"] = output_path
        del result["drawing"]  # not serializable

        return result


# --------------------------------------------------
# CLI
# --------------------------------------------------

if __name__ == "__main__":
    import sys

    blueprint_file = sys.argv[1] if len(sys.argv) > 1 else "circuit_blueprints.json"

    with open(blueprint_file, "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    compiler = CircuitCompiler()
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    print("=" * 64)
    print("  CIRCUIT COMPILER REPORT")
    print("=" * 64)

    results = []
    for bp in blueprints:
        qid = bp.get("question_id", "?")
        out_path = str(output_dir / f"{qid}.svg")

        result = compiler.compile_to_svg(bp, out_path)
        results.append(result)

        status = result["status"]
        print(f"\n  {qid}: {status}")

        if status == "FAILED":
            for err in result.get("errors", []):
                print(f"    ERROR: {err}")
            continue

        topo = result["topology"]
        soln = result["solution"]
        print(f"    Nodes: {topo['node_count']}, Components: {topo['component_count']}")
        print(f"    Layout: {result['layout']['layout_type']}")
        print(f"    Solution: {soln.get('circuit_mode', '?')}")
        print(f"    Output: {result['output_file']}")

    passed = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] == "FAILED")

    print(f"\n{'=' * 64}")
    print(f"  COMPILATION COMPLETE: {passed} passed, {failed} failed")
    print(f"{'=' * 64}")
