from typing import Dict, List

from physics_solver import PhysicsSolver


_ALLOWED_SCENARIOS = {
    "beyond_2f",
    "at_2f",
    "between_f_and_2f",
    "inside_f",
}

_ALLOWED_RAYS = {
    "parallel_ray",
    "optical_center_ray",
    "focal_ray",
}


class RayValidation:

    def __init__(self, focal_length: float = 100.0):
        self.solver = PhysicsSolver(focal_length=focal_length)

    # =====================================================
    # PUBLIC API
    # =====================================================

    def validate(self, blueprint: Dict) -> Dict:

        errors = []

        errors.extend(self._validate_schema(blueprint))

        if errors:
            return {
                "valid": False,
                "errors": errors,
            }

        errors.extend(self._validate_lens(blueprint))
        errors.extend(self._validate_focal_points(blueprint))
        errors.extend(self._validate_object(blueprint))
        errors.extend(self._validate_rays(blueprint))
        errors.extend(self._validate_scenario(blueprint))
        errors.extend(self._validate_physics(blueprint))

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    # =====================================================
    # SCHEMA
    # =====================================================

    def _validate_schema(self, bp: Dict) -> List[str]:

        required = [
            "question_id",
            "renderer_type",
            "scenario",
            "principal_axis",
            "lens",
            "focal_points",
            "object",
            "rays",
        ]

        errors = []

        for field in required:
            if field not in bp:
                errors.append(f"Missing field: {field}")

        if bp.get("renderer_type") != "ray":
            errors.append("renderer_type must be 'ray'")

        return errors

    # =====================================================
    # LENS
    # =====================================================

    def _validate_lens(self, bp: Dict) -> List[str]:

        errors = []

        lens = bp["lens"]

        if lens.get("type") != "convex":
            errors.append("Only convex lens currently supported")

        if lens.get("height", 0) <= 0:
            errors.append("Lens height must be > 0")

        if lens.get("x") is None:
            errors.append("Lens x-coordinate missing")

        return errors

    # =====================================================
    # FOCAL POINTS
    # =====================================================

    def _validate_focal_points(self, bp: Dict) -> List[str]:

        errors = []

        fp = bp["focal_points"]

        required = [
            "F1",
            "F2",
            "2F1",
            "2F2",
        ]

        for key in required:
            if key not in fp:
                errors.append(f"Missing focal point {key}")

        if errors:
            return errors

        f1 = fp["F1"]
        f2 = fp["F2"]
        tf1 = fp["2F1"]
        tf2 = fp["2F2"]

        if not (tf1 < f1):
            errors.append("Expected: 2F1 < F1")

        if not (f1 < f2):
            errors.append("Expected: F1 < F2")

        if not (f2 < tf2):
            errors.append("Expected: F2 < 2F2")

        return errors

    # =====================================================
    # OBJECT
    # =====================================================

    def _validate_object(self, bp: Dict) -> List[str]:

        errors = []

        obj = bp["object"]

        if "x" not in obj:
            errors.append("Object x missing")

        if "height" not in obj:
            errors.append("Object height missing")

        if obj.get("height", 0) <= 0:
            errors.append("Object height must be > 0")

        return errors

    # =====================================================
    # RAYS
    # =====================================================

    def _validate_rays(self, bp: Dict) -> List[str]:

        errors = []

        rays = bp["rays"]

        if len(rays) == 0:
            errors.append("No rays defined")
            return errors

        for idx, ray in enumerate(rays):

            ray_type = ray.get("type")

            if ray_type not in _ALLOWED_RAYS:
                errors.append(
                    f"Invalid ray type at index {idx}: {ray_type}"
                )

        return errors

    # =====================================================
    # SCENARIO RULES
    # =====================================================

    def _validate_scenario(self, bp: Dict) -> List[str]:

        errors = []

        scenario = bp["scenario"]

        if scenario not in _ALLOWED_SCENARIOS:
            errors.append(f"Unsupported scenario: {scenario}")
            return errors

        obj_x = bp["object"]["x"]

        f1 = bp["focal_points"]["F1"]
        tf1 = bp["focal_points"]["2F1"]

        if scenario == "beyond_2f":

            if not obj_x < tf1:
                errors.append(
                    "Object should be beyond 2F1"
                )

        elif scenario == "at_2f":

            if obj_x != tf1:
                errors.append(
                    "Object should be at 2F1"
                )

        elif scenario == "between_f_and_2f":

            if not (tf1 < obj_x < f1):
                errors.append(
                    "Object should lie between F1 and 2F1"
                )

        elif scenario == "inside_f":

            if not (f1 < obj_x):
                errors.append(
                    "Object should lie between lens and F1"
                )

        return errors

    # =====================================================
    # PHYSICS VALIDATION
    # =====================================================

    def _validate_physics(self, bp: Dict) -> List[str]:

        errors = []

        scenario = bp["scenario"]

        lens_x = bp["lens"]["x"]

        object_x = bp["object"]["x"]

        object_height = bp["object"]["height"]

        result = self.solver.solve_convex_lens(
            lens_x=lens_x,
            object_x=object_x,
            object_height=object_height,
            scenario=scenario,
        )

        image_type = result["image_type"]
        orientation = result["orientation"]

        image_height = result["image_height"]

        if scenario == "beyond_2f":

            if image_type != "real":
                errors.append("Expected real image")

            if orientation != "inverted":
                errors.append("Expected inverted image")

            if image_height >= object_height:
                errors.append(
                    "Expected diminished image"
                )

        elif scenario == "at_2f":

            if image_type != "real":
                errors.append("Expected real image")

            if orientation != "inverted":
                errors.append("Expected inverted image")

            if abs(image_height - object_height) > 5:
                errors.append(
                    "Expected same-size image"
                )

        elif scenario == "between_f_and_2f":

            if image_type != "real":
                errors.append("Expected real image")

            if orientation != "inverted":
                errors.append("Expected inverted image")

            if image_height <= object_height:
                errors.append(
                    "Expected magnified image"
                )

        elif scenario == "inside_f":

            if image_type != "virtual":
                errors.append("Expected virtual image")

            if orientation != "erect":
                errors.append("Expected erect image")

            if image_height <= object_height:
                errors.append(
                    "Expected magnified image"
                )

        return errors


# =========================================================
# TEST RUNNER
# =========================================================

if __name__ == "__main__":

    import json
    import os

    with open("data/physics_blueprints.json", "r") as f:
        blueprints = json.load(f)

    validator = RayValidation()

    output_lines = []
    output_lines.append("\nRAY VALIDATION REPORT\n")

    for bp in blueprints:

        result = validator.validate(bp)

        output_lines.append("=" * 60)
        output_lines.append(f"QUESTION : {bp['question_id']}")
        output_lines.append(f"VALID    : {result['valid']}")

        if result["errors"]:

            for err in result["errors"]:
                output_lines.append(f"  - {err}")

        else:
            output_lines.append("  ✓ Passed")

    # Print to terminal
    for line in output_lines:
        print(line)

    # Save to file c:\CODES\VQP\approch2\ray\validate.txt
    output_path = os.path.join(os.path.dirname(__file__), "validate.txt")
    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(output_lines) + "\n")