"""
Ray Integration Test

Validates AI-generated blueprints against the compiler contract.

Usage:
    python -m pytest backend_v2/tests/test_ray_integration.py -v
    python backend_v2/tests/test_ray_integration.py
"""

import json
import sys
import os
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(BASE / "approch2" / "ray"))
sys.path.insert(0, str(BASE / "approch2"))
sys.path.insert(0, str(BASE / "backend_v2"))


VALID_SCENARIOS = {
    "beyond_2f",
    "at_2f",
    "between_f_and_2f",
    "inside_f",
}

VALID_RAY_TYPES = {
    "parallel_ray",
    "optical_center_ray",
    "focal_ray",
}


def load_json(relative_path):
    path = BASE / relative_path
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_schema_structure():
    """Verify ray_schema.json has all fields required by the compiler."""
    schema = load_json("backend_v2/schemas/ray/ray_schema.json")

    required = {
        "question_id", "renderer_type", "scenario",
        "principal_axis", "lens", "focal_points", "object", "rays",
    }
    for field in required:
        assert field in schema, f"Schema missing required field: {field}"

    assert schema["renderer_type"] == "ray", "renderer_type must be 'ray'"

    assert isinstance(schema["principal_axis"], dict), (
        "principal_axis must be a dict, not bool"
    )

    lens = schema["lens"]
    assert "type" in lens, "lens missing 'type'"
    assert "x" in lens, "lens missing 'x'"
    assert "height" in lens, "lens missing 'height'"

    assert isinstance(schema["rays"], list), "rays must be a list"
    if len(schema["rays"]) > 0:
        first_ray = schema["rays"][0]
        assert isinstance(first_ray, dict), "ray must be a dict"
        assert "type" in first_ray, "ray missing 'type' field"


def test_examples_pass_validation():
    """Verify every example blueprint passes ray_validation.py."""
    from ray_validation import RayValidation

    examples = load_json("backend_v2/schemas/ray/examples.json")
    validator = RayValidation()
    failures = []

    for i, example in enumerate(examples):
        blueprint = example["blueprint"]
        result = validator.validate(blueprint)
        if not result["valid"]:
            failures.append(
                f"Example {i} ({blueprint.get('question_id', '?')}): "
                f"{'; '.join(result['errors'])}"
            )

    if failures:
        print("\nVALIDATION FAILURES:")
        for f in failures:
            print(f"  - {f}")
    assert not failures, (
        f"{len(failures)} example(s) failed validation"
    )


def test_each_scenario():
    """Create a minimal valid blueprint for each scenario and validate."""
    from ray_validation import RayValidation

    validator = RayValidation()

    scenarios = {
        "beyond_2f": {"x": 150, "height": 80},
        "at_2f": {"x": 200, "height": 80},
        "between_f_and_2f": {"x": 250, "height": 80},
        "inside_f": {"x": 350, "height": 80},
    }

    base = {
        "question_id": "test_scenario",
        "renderer_type": "ray",
        "diagram_family": "Convex Lens",
        "principal_axis": {"y": 300},
        "lens": {
            "type": "convex",
            "x": 400,
            "height": 250,
        },
        "focal_points": {
            "F1": 300,
            "2F1": 200,
            "F2": 500,
            "2F2": 600,
        },
    }

    for scenario, obj in scenarios.items():
        blueprint = {
            **base,
            "scenario": scenario,
            "object": obj,
            "rays": [
                {"type": "parallel_ray"},
                {"type": "optical_center_ray"},
            ],
        }
        result = validator.validate(blueprint)
        assert result["valid"], (
            f"Scenario '{scenario}' failed: "
            f"{'; '.join(result['errors'])}"
        )


def test_invalid_scenario_rejected():
    """Verify invalid scenario values are rejected."""
    from ray_validation import RayValidation

    validator = RayValidation()

    blueprint = {
        "question_id": "test_invalid",
        "renderer_type": "ray",
        "scenario": "invalid_scenario",
        "principal_axis": {"y": 300},
        "lens": {"type": "convex", "x": 400, "height": 250},
        "focal_points": {"F1": 300, "2F1": 200, "F2": 500, "2F2": 600},
        "object": {"x": 250, "height": 80},
        "rays": [{"type": "parallel_ray"}],
    }
    result = validator.validate(blueprint)
    assert not result["valid"]
    assert any("scenario" in e for e in result["errors"])


def test_missing_field_rejected():
    """Verify missing required fields are rejected."""
    from ray_validation import RayValidation

    validator = RayValidation()

    blueprint = {
        "renderer_type": "ray",
        "principal_axis": {"y": 300},
        "lens": {"type": "convex", "x": 400, "height": 250},
    }
    result = validator.validate(blueprint)
    assert not result["valid"]
    missing = [e for e in result["errors"] if e.startswith("Missing field")]
    assert len(missing) > 0


def test_merge_schema_with_examples():
    """Verify _merge_schema produces valid blueprints from examples."""
    from ray_validation import RayValidation

    schema = load_json("backend_v2/schemas/ray/ray_schema.json")
    examples = load_json("backend_v2/schemas/ray/examples.json")
    validator = RayValidation()

    for example in examples:
        blueprint = example["blueprint"]

        merged = schema.copy()
        merged.update(blueprint)
        for key in schema:
            if (
                isinstance(schema[key], dict)
                and key in blueprint
                and isinstance(blueprint[key], dict)
            ):
                merged[key] = {**schema[key], **blueprint[key]}

        result = validator.validate(merged)
        assert result["valid"], (
            f"Merged blueprint '{blueprint.get('question_id', '?')}' "
            f"failed: {'; '.join(result['errors'])}"
        )


def test_blueprint_generator_prompt():
    """Verify blueprint_generator prompt includes compiler contract rules."""
    gen_path = (
        BASE / "backend_v2" / "diagram_intelligence"
        / "blueprint_generator" / "blueprint_generator.py"
    )
    with open(gen_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "MUST conform" in content, (
        "Prompt must contain 'MUST conform' instruction"
    )
    assert "scenario" in content, (
        "Prompt must mention scenario field"
    )
    assert "All ray types" in content or "Allowed ray types" in content or '"parallel_ray"' in content, (
        "Prompt must list allowed ray types"
    )


def test_compiler_accepts_examples():
    """Verify compiler accepts example blueprints without ValueError."""
    from approch2.ray.ray_compiler import RayCompiler

    examples = load_json("backend_v2/schemas/ray/examples.json")
    compiler = RayCompiler()
    failures = []

    for example in examples:
        blueprint = example["blueprint"]
        try:
            compiler.compile(blueprint)
        except ValueError as e:
            failures.append(
                f"Compiler rejected '{blueprint.get('question_id', '?')}': {e}"
            )

    if failures:
        print("\nCOMPILER FAILURES:")
        for f in failures:
            print(f"  - {f}")
    assert not failures, (
        f"{len(failures)} blueprint(s) rejected by compiler"
    )


if __name__ == "__main__":
    print("=" * 60)
    print("RAY INTEGRATION TEST")
    print("=" * 60)

    tests = [
        ("Schema structure", test_schema_structure),
        ("Examples pass validation", test_examples_pass_validation),
        ("Each scenario valid", test_each_scenario),
        ("Invalid scenario rejected", test_invalid_scenario_rejected),
        ("Missing field rejected", test_missing_field_rejected),
        ("Merge schema with examples", test_merge_schema_with_examples),
        ("Blueprint generator prompt", test_blueprint_generator_prompt),
        ("Compiler accepts examples", test_compiler_accepts_examples),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")

    sys.exit(1 if failed > 0 else 0)
