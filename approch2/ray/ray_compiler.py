"""
ray_compiler.py

Ray Optics Compiler

Pipeline:

Blueprint
    ↓
Validation
    ↓
Physics Solver
    ↓
SVG Renderer
    ↓
SVG Output
"""

import os
from pathlib import Path
from typing import Dict

from ray_validation import RayValidation
from renderers.ray_renderer import RayRenderer


class RayCompiler:

    def __init__(self):

        self.validator = RayValidation()
        self.renderer = RayRenderer()

    # =====================================================
    # Compile
    # =====================================================

    def compile(self, blueprint: Dict) -> str:

        validation = self.validator.validate(blueprint)

        if not validation["valid"]:

            errors = "\n".join(validation["errors"])

            raise ValueError(
                f"Ray Validation Failed\n\n{errors}"
            )

        svg = self._render(blueprint)

        return svg

    # =====================================================
    # Render Dispatcher
    # =====================================================

    def _render(self, blueprint: Dict) -> str:

        diagram_family = (
            blueprint.get("diagram_family", "")
            .lower()
            .strip()
        )

        lens_type = (
            blueprint.get("lens", {})
            .get("type", "")
            .lower()
            .strip()
        )

        if diagram_family == "convex lens":
            return self.renderer.render_convex_lens(
                blueprint
            )

        if lens_type == "convex":
            return self.renderer.render_convex_lens(
                blueprint
            )

        raise ValueError(
            f"Unsupported ray diagram: {diagram_family}"
        )

    # =====================================================
    # Compile + Save
    # =====================================================

    def compile_to_file(
        self,
        blueprint: Dict,
        output_path: str,
    ) -> str:

        svg = self.compile(blueprint)

        output_file = Path(output_path)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file.write_text(
            svg,
            encoding="utf-8",
        )

        return str(output_file)

    # =====================================================
    # Batch Compile
    # =====================================================

    def compile_many(
        self,
        blueprints: list,
        output_dir: str = r"C:\CODES\VQP\approch2\ray\data",
    ):

        results = []

        output_dir = Path(output_dir)
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        for blueprint in blueprints:

            question_id = blueprint.get(
                "question_id",
                "unknown",
            )

            try:

                output_path = (
                    output_dir /
                    f"{question_id}.svg"
                )

                self.compile_to_file(
                    blueprint,
                    str(output_path),
                )

                results.append(
                    {
                        "question_id": question_id,
                        "status": "success",
                        "file": str(output_path),
                    }
                )

            except Exception as e:

                results.append(
                    {
                        "question_id": question_id,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return results


# =========================================================
# TEST RUNNER
# =========================================================

if __name__ == "__main__":

    import json

    compiler = RayCompiler()

    blueprint_path = "data/physics_blueprints.json"
    if not os.path.exists(blueprint_path):
        blueprint_path = os.path.join(os.path.dirname(__file__), "..", "data", "physics_blueprints.json")
    if not os.path.exists(blueprint_path):
        blueprint_path = os.path.join(os.path.dirname(__file__), "data", "physics_blueprints.json")

    with open(
        blueprint_path,
        "r",
        encoding="utf-8",
    ) as f:

        blueprints = json.load(f)

    results = compiler.compile_many(
        blueprints,
        output_dir=r"C:\CODES\VQP\approch2\ray\data",
    )

    print("\nRAY COMPILER REPORT\n")

    for result in results:

        print("=" * 60)

        print(
            result["question_id"],
            "->",
            result["status"],
        )

        if result["status"] == "failed":

            print(
                "ERROR:",
                result["error"],
            )

        else:

            print(
                "FILE:",
                result["file"],
            )
