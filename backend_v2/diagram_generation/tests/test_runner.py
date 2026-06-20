"""
End-to-end diagram generation test runner (Phase 4.3, Task 3).

Runs the full pipeline for each family:

    Question -> Classify -> Retrieve/Generate -> Adapt -> Compile -> SVG

Validates every step and produces a PASS/FAIL report.
"""

import json
import sys
import time
from pathlib import Path


def _print(text=""):
    try:
        print(text)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "utf-8"
        print(text.encode(enc, errors="replace").decode(enc))

BACKEND_V2 = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_V2))

from pipeline.diagram_pipeline import (
    COMPILED_SVG_DIR,
    ADAPTERS,
    _load_schema,
    _merge_schema,
    _normalize_blueprint,
    compile_and_check,
)
from diagram_generation.example_retriever import retrieve
from diagram_generation.blueprint_modifier import BlueprintModifier
from diagram_generation.schema_blueprint_generator import SchemaBlueprintGenerator
from diagram_generation.family_validator import validate as validate_family

TESTS_DIR = BACKEND_V2 / "tests" / "diagram_tests"
SIMILARITY_THRESHOLD = 0.85


# ---------------------------------------------------------------------------
# SVG validation (Task 4)
# ---------------------------------------------------------------------------

REQUIRED_LABELS = {
    "ray": ["Object", "Image", "F\u2081"],
    "circuit": ["V", "A", "\u03a9"],
    "fbd": ["mg", "N", "f"],
    "magnetic": ["N", "S"],
    "semiconductor": ["p", "n"],
    "graph": ["V", "I", "t"],
}


def validate_svg(path: Path, family: str) -> dict:
    if not path.exists():
        return {"valid": False, "error": "File not found", "size": 0}
    size = path.stat().st_size
    if size == 0:
        return {"valid": False, "error": "Empty file", "size": 0}
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"valid": False, "error": f"Read error: {e}", "size": size}

    if "<svg" not in content:
        return {"valid": False, "error": "Missing <svg> tag", "size": size}
    if "</svg>" not in content:
        return {"valid": False, "error": "Missing </svg> tag", "size": size}

    expected = REQUIRED_LABELS.get(family, [])
    missing = [label for label in expected if label not in content]
    if missing:
        return {
            "valid": True,
            "warning": f"Missing expected labels: {missing}",
            "size": size,
        }

    return {"valid": True, "size": size}


# ---------------------------------------------------------------------------
# Stale SVG cleanup (Task 7)
# ---------------------------------------------------------------------------


def cleanup_svg(question_id: str):
    for f in COMPILED_SVG_DIR.glob(f"*{question_id}*.svg"):
        _print(f"  [CLEANUP] Deleting stale SVG: {f.name}")
        f.unlink()


# ---------------------------------------------------------------------------
# Blueprint generation (skips LLM if blueprint already exists)
# ---------------------------------------------------------------------------


def generate_blueprint(question: str, family: str, question_id: str) -> dict:
    schema = _load_schema(family)
    retrieval = retrieve(question, family)
    similarity = retrieval["similarity_score"]
    best_match = retrieval["best_match"]
    example_bp = best_match.get("blueprint", best_match)

    _print(f"  Similarity score: {similarity}")

    if similarity >= SIMILARITY_THRESHOLD:
        mode = "EXAMPLE_BASED"
        _print(f"  Mode: {mode}")
        modifier = BlueprintModifier()
        result = modifier.modify_blueprint(question, family, schema, example_bp)
        blueprint = _normalize_blueprint(result.get("blueprint"))
    else:
        mode = "SCHEMA_BASED"
        _print(f"  Mode: {mode}")
        generator = SchemaBlueprintGenerator()
        result = generator.generate_blueprint(question, family, schema)
        blueprint = _normalize_blueprint(result.get("blueprint"))

    merged = _merge_schema(blueprint, family) if isinstance(blueprint, dict) else blueprint

    return {
        "blueprint": blueprint,
        "merged": merged,
        "mode": mode,
        "similarity": similarity,
    }


# ---------------------------------------------------------------------------
# Single test-case runner
# ---------------------------------------------------------------------------


def run_test(test: dict) -> dict:
    qid = test["question_id"]
    question = test["question"]
    family = test["expected_family"]
    result = {
        "question_id": qid,
        "question": question,
        "family": family,
        "validation": None,
        "adapter": None,
        "compiler": None,
        "svg": None,
        "status": "FAILED",
        "error": None,
        "duration": 0,
    }

    t0 = time.time()

    # ---- Step 0: Cleanup stale SVGs ----
    _print(f"\n  Cleaning up old SVGs...")
    cleanup_svg(qid)

    # ---- Step 1: Family validation ----
    _print(f"  Validating family...")
    v = validate_family(question, family)
    result["validation"] = v
    if not v["valid"]:
        result["error"] = f"Family validation failed: {v['reason']}"
        result["duration"] = time.time() - t0
        return result
    _print(f"  Family validation: PASS")

    # ---- Step 2: Blueprint generation ----
    _print(f"  Generating blueprint...")
    try:
        bp_result = generate_blueprint(question, family, qid)
    except Exception as e:
        result["error"] = f"Blueprint generation failed: {e}"
        result["duration"] = time.time() - t0
        return result

    blueprint = bp_result["blueprint"]
    if not isinstance(blueprint, dict):
        result["error"] = "Blueprint is not a dict"
        result["duration"] = time.time() - t0
        return result

    _print(f"  Blueprint generation: OK")

    # ---- Step 3: Adapter ----
    _print(f"  Adapting blueprint...")
    adapt_fn = ADAPTERS.get(family)
    if not adapt_fn:
        result["error"] = f"No adapter for family: {family}"
        result["duration"] = time.time() - t0
        return result

    try:
        adapted = adapt_fn(blueprint)
    except Exception as e:
        result["error"] = f"Adapter failed: {e}"
        result["duration"] = time.time() - t0
        return result

    result["adapter"] = adapted
    _print(f"  Adapter: OK")
    _print(f"  Adapted fields: {list(adapted.keys())}")

    # ---- Step 4: Compile + check ----
    _print(f"  Compiling...")
    output_filename = f"test_{qid}.svg"
    output_path = COMPILED_SVG_DIR / output_filename

    try:
        compile_and_check(family, adapted, output_path)
        result["compiler"] = "PASS"
        _print(f"  Compiler: PASS")
    except Exception as e:
        result["error"] = f"Compilation failed: {e}"
        result["duration"] = time.time() - t0
        return result

    # ---- Step 5: SVG validation ----
    _print(f"  Validating SVG...")
    svg_check = validate_svg(output_path, family)
    result["svg"] = svg_check
    if svg_check["valid"]:
        _print(f"  SVG: PASS ({svg_check['size']} bytes)")
        if svg_check.get("warning"):
            _print(f"  SVG warning: {svg_check['warning']}")
    else:
        result["error"] = f"SVG validation failed: {svg_check['error']}"
        result["duration"] = time.time() - t0
        return result

    result["status"] = "PASS"
    result["duration"] = round(time.time() - t0, 2)
    return result


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------


def print_report(results: list):
    _print()
    _print("=" * 70)
    _print("  DIAGRAM GENERATION TEST REPORT")
    _print("=" * 70)

    passes = 0
    failures = 0

    for r in results:
        status_symbol = "✓" if r["status"] == "PASS" else "✗"
        _print()
        _print(f"  {status_symbol} {r['question_id']} ({r['family']})")
        _print(f"     Status : {r['status']}")
        _print(f"     Time   : {r['duration']}s")
        if r.get("validation"):
            _print(f"     Family : {'PASS' if r['validation']['valid'] else 'FAIL'}")
        if r.get("compiler"):
            _print(f"     Compile: {r['compiler']}")
        if r.get("svg"):
            svg = r["svg"]
            _print(f"     SVG    : {'PASS' if svg['valid'] else 'FAIL'} ({svg.get('size', 0)} bytes)")
            if svg.get("warning"):
                _print(f"     Warning: {svg['warning']}")
        if r["error"]:
            _print(f"     Error  : {r['error']}")

        if r["status"] == "PASS":
            passes += 1
        else:
            failures += 1

    _print()
    _print("=" * 70)
    _print(f"  TOTAL: {passes} passed, {failures} failed")
    _print(f"  RESULTS: {passes}/{len(results)}")
    _print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    families = ["circuit", "ray", "fbd", "magnetic", "semiconductor", "graph"]

    if len(sys.argv) > 1:
        families = [sys.argv[1]]

    all_results = []

    for family in families:
        test_file = TESTS_DIR / f"test_{family}.json"
        if not test_file.exists():
            _print(f"\n  [SKIP] No test file for {family}: {test_file}")
            continue

        with open(test_file, "r", encoding="utf-8") as f:
            tests = json.load(f)

        _print()
        _print(f"{'=' * 70}")
        _print(f"  FAMILY: {family.upper()}")
        _print(f"{'=' * 70}")

        for test in tests:
            _print()
            _print(f"  --- {test['question_id']}: {test['question'][:60]}... ---")
            r = run_test(test)
            all_results.append(r)

    print_report(all_results)


if __name__ == "__main__":
    main()
