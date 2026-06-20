"""
End-to-end pipeline test for the VisualQ Diagram Intelligence system.

Usage:
    python backend_v2/test.py

Runs the full pipeline (Classifier -> Schema Router -> Blueprint Generator
-> Compiler Router -> SVG) against 11 hardcoded questions spanning all
supported diagram families.
"""

import json
import sys
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup – mirrors diagram_intelligence/compiler_router.py
# ---------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
BACKEND_V2 = Path(__file__).resolve().parent

sys.path.insert(0, str(BACKEND_V2))
sys.path.insert(0, str(BASE))

for sub in ("ray", "circuit", "fbd", "magnetic_field", "semiconductor", "graph"):
    sys.path.insert(0, str(BASE / "approch2" / sub))

# ---------------------------------------------------------------------------
# Import pipeline components
# ---------------------------------------------------------------------------

try:
    from diagram_intelligence.classifier.llm_classifier import DiagramClassifier
except Exception as e:
    DiagramClassifier = None
    _classifier_import_err = str(e)

try:
    from diagram_intelligence.blueprint_generator.blueprint_generator import (
        BlueprintGenerator,
    )
except Exception as e:
    BlueprintGenerator = None
    _generator_import_err = str(e)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUESTIONS = [
    "Draw a ray diagram for an object placed between F1 and 2F1 of a convex lens.",
    "Draw a free body diagram of a hanging mass.",
    "Draw a free body diagram of a block resting on a rough horizontal surface.",
    "Draw a circuit containing a cell, resistor and ammeter connected in series.",
    "Draw the meter bridge arrangement used to determine an unknown resistance.",
    "Draw magnetic field lines around a straight current carrying conductor.",
    "Draw the magnetic field pattern of a bar magnet.",
    "Draw the forward bias arrangement of a PN junction diode.",
    "Draw the symbol of an LED.",
    "Draw the V-I characteristics of a semiconductor diode.",
    "Draw a distance-time graph for uniform motion.",
]

OUTPUT_DIR = BACKEND_V2 / "test_output"
SCHEMA_DIR = BACKEND_V2 / "schemas"
REPORT_FILE = OUTPUT_DIR / "test_report.json"

# ---------------------------------------------------------------------------
# Compile functions (mirror diagram_intelligence/compiler_router.py)
# ---------------------------------------------------------------------------

COMPILERS = {}


def _import_compilers():
    global COMPILERS

    try:
        from approch2.ray.ray_compiler import RayCompiler

        def _compile_ray(bp, dst):
            RayCompiler().compile_to_file(bp, str(dst))

        COMPILERS["ray"] = _compile_ray
    except Exception as e:
        COMPILERS["ray"] = lambda bp, dst: (_ for _ in ()).throw(
            RuntimeError(f"Ray compiler unavailable: {e}")
        )

    try:
        from approch2.circuit.circuit_compiler import CircuitCompiler

        def _compile_circuit(bp, dst):
            CircuitCompiler().compile_to_file(bp, str(dst))

        COMPILERS["circuit"] = _compile_circuit
    except Exception as e:
        COMPILERS["circuit"] = lambda bp, dst: (_ for _ in ()).throw(
            RuntimeError(f"Circuit compiler unavailable: {e}")
        )

    try:
        from approch2.fbd.fbd_layout import generate_layout as fbd_layout
        from approch2.fbd.fbd_renderer import render_svg as fbd_render

        def _compile_fbd(bp, dst):
            layout = fbd_layout(bp)
            svg = fbd_render(layout)
            dst.write_text(svg, encoding="utf-8")

        COMPILERS["fbd"] = _compile_fbd
    except Exception as e:
        COMPILERS["fbd"] = lambda bp, dst: (_ for _ in ()).throw(
            RuntimeError(f"FBD compiler unavailable: {e}")
        )

    try:
        from approch2.magnetic_field.mf_layout import generate_layout as mf_layout
        from approch2.magnetic_field.mf_field_engine import generate_field as mf_field
        from approch2.magnetic_field.mf_renderer import render_svg as mf_render

        def _compile_magnetic(bp, dst):
            layout = mf_layout(bp)
            mf_field(bp.get("object_type", ""))
            svg = mf_render(layout)
            dst.write_text(svg, encoding="utf-8")

        COMPILERS["magnetic"] = _compile_magnetic
    except Exception as e:
        COMPILERS["magnetic"] = lambda bp, dst: (_ for _ in ()).throw(
            RuntimeError(f"Magnetic compiler unavailable: {e}")
        )

    try:
        from approch2.semiconductor.semi_layout import generate_layout as semi_layout
        from approch2.semiconductor.semi_renderer import render_svg as semi_render

        def _compile_semiconductor(bp, dst):
            layout = semi_layout(bp)
            svg = semi_render(layout)
            dst.write_text(svg, encoding="utf-8")

        COMPILERS["semiconductor"] = _compile_semiconductor
    except Exception as e:
        COMPILERS["semiconductor"] = lambda bp, dst: (_ for _ in ()).throw(
            RuntimeError(f"Semiconductor compiler unavailable: {e}")
        )

    try:
        from approch2.graph.graph_renderer import render_graph

        def _compile_graph(bp, dst):
            render_graph(bp.get("object_type", ""), dst)

        COMPILERS["graph"] = _compile_graph
    except Exception as e:
        COMPILERS["graph"] = lambda bp, dst: (_ for _ in ()).throw(
            RuntimeError(f"Graph compiler unavailable: {e}")
        )


# ---------------------------------------------------------------------------
# Schema merge (mirror diagram_intelligence/compiler_router.py)
# ---------------------------------------------------------------------------


def _merge_schema(blueprint, family):
    if not isinstance(blueprint, dict):
        return blueprint

    schema_file = SCHEMA_DIR / family / f"{family}_schema.json"
    if not schema_file.exists():
        return blueprint

    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    if not isinstance(schema, dict):
        return blueprint

    merged = schema.copy()
    if isinstance(blueprint, dict):
        merged.update(blueprint)

    for key in schema:
        if (
            isinstance(schema[key], dict)
            and key in blueprint
            and isinstance(blueprint[key], dict)
        ):
            merged[key] = {**schema[key], **blueprint[key]}

    return merged


# ---------------------------------------------------------------------------
# Single-question pipeline runner
# ---------------------------------------------------------------------------


def run_pipeline(question, classifier, generator, question_index=0):
    step_results = {
        "classify": None,
        "family": None,
        "generate": None,
        "compile": None,
        "status": "UNKNOWN",
        "error": None,
    }

    # ---- Step 1: Classify --------------------------------------------------
    try:
        classification = classifier.classify(question)
        step_results["classify"] = classification

        diagram_required = classification.get("diagram_required", False)
        family = classification.get("family", "").lower().strip()

        if not diagram_required:
            step_results["status"] = "SKIPPED (no diagram required)"
            step_results["error"] = "Classifier returned diagram_required=false"
            return step_results

        if family not in COMPILERS:
            step_results["status"] = "SKIPPED (unknown family)"
            step_results["error"] = f"Unknown family: {family}"
            step_results["family"] = family
            return step_results

        step_results["family"] = family

    except Exception as e:
        step_results["status"] = "FAILED"
        step_results["error"] = f"Classification failed: {e}"
        step_results["traceback"] = traceback.format_exc()
        return step_results

    # ---- Step 2: Generate blueprint ----------------------------------------
    try:
        result = generator.generate_blueprint(question, family)
        blueprint = result.get("blueprint", {})

        # Normalize: LLM may return a list (e.g. copied from examples array)
        if isinstance(blueprint, list):
            if len(blueprint) == 1 and isinstance(blueprint[0], dict):
                blueprint = blueprint[0]
            elif len(blueprint) > 0 and isinstance(blueprint[0], dict):
                # Has a "blueprint" key? Use that.
                if "blueprint" in blueprint[0]:
                    blueprint = blueprint[0]["blueprint"]
                else:
                    blueprint = blueprint[0]

        if not isinstance(blueprint, dict):
            step_results["status"] = "FAILED"
            step_results["error"] = (
                f"Blueprint is not a dict (got {type(blueprint).__name__}): "
                f"{json.dumps(blueprint, indent=2)[:500]}"
            )
            return step_results
        step_results["generate"] = blueprint
    except Exception as e:
        step_results["status"] = "FAILED"
        step_results["error"] = f"Blueprint generation failed: {e}"
        step_results["traceback"] = traceback.format_exc()
        return step_results

    # ---- Step 3: Merge with schema template --------------------------------
    try:
        blueprint = _merge_schema(blueprint, family)
        step_results["generate"] = blueprint
    except Exception as e:
        step_results["status"] = "FAILED"
        step_results["error"] = f"Schema merge failed: {e}"
        step_results["traceback"] = traceback.format_exc()
        return step_results

    # ---- Step 4: Compile to SVG --------------------------------------------
    qid = blueprint.get("question_id")
    if not qid or not isinstance(qid, str) or qid.strip() == "":
        qid = f"Q{question_index+1:02d}_{family}"
    else:
        # Prefix with index to avoid collisions
        qid = f"Q{question_index+1:02d}_{qid}"
    safe_qid = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in str(qid))
    svg_path = OUTPUT_DIR / family / f"{safe_qid}.svg"
    svg_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        COMPILERS[family](blueprint, svg_path)
        step_results["status"] = "SUCCESS"
        step_results["compile"] = str(svg_path)
    except Exception as e:
        step_results["status"] = "FAILED"
        step_results["error"] = f"Compilation failed: {e}"
        step_results["traceback"] = traceback.format_exc()

    return step_results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    _import_compilers()

    # Instantiate pipeline components
    classifier_ok = True
    try:
        classifier = DiagramClassifier()
    except Exception as e:
        classifier = None
        classifier_ok = False
        _classifier_err = str(e)

    generator_ok = True
    try:
        generator = BlueprintGenerator()
    except Exception as e:
        generator = None
        generator_ok = False
        _generator_err = str(e)

    # ---- Run pipeline for each question ------------------------------------
    results = []

    for idx, question in enumerate(QUESTIONS):
        qnum = idx + 1

        if not classifier_ok:
            results.append({
                "question": question,
                "family": None,
                "status": "FAILED",
                "error": f"Classifier unavailable: {_classifier_err}",
                "svg_path": None,
            })
            continue

        if not generator_ok:
            results.append({
                "question": question,
                "family": None,
                "status": "FAILED",
                "error": f"BlueprintGenerator unavailable: {_generator_err}",
                "svg_path": None,
            })
            continue

        step = run_pipeline(question, classifier, generator, question_index=idx)

        family = step.get("family")
        status = step["status"]
        svg_path = step.get("compile")

        results.append({
            "question": question,
            "family": family,
            "status": status,
            "error": step.get("error"),
            "svg_path": svg_path,
        })

    # ---- Save report -------------------------------------------------------
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # ---- Print console report ----------------------------------------------
    header = f"""
{'=' * 60}
TEST PIPELINE REPORT
{'=' * 60}
"""
    print(header)

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for idx, r in enumerate(results):
        qnum = idx + 1
        status = r["status"]
        family = r["family"] or "N/A"

        if status == "SUCCESS":
            success_count += 1
        elif status.startswith("SKIPPED"):
            skipped_count += 1
        else:
            failed_count += 1

        print(f"Q{qnum}")
        print(f"Question : {r['question']}")
        print(f"Family   : {family}")
        print(f"Status   : {status}")

        if r.get("svg_path"):
            print(f"SVG      : {r['svg_path']}")
        if r.get("error"):
            print(f"Error    : {r['error']}")

        if idx < len(QUESTIONS) - 1:
            print()
            print("---")
            print()

    summary = f"""
{'=' * 60}
SUMMARY
{'=' * 60}

Total Questions : {len(QUESTIONS)}
Success         : {success_count}
Failed          : {failed_count}
Skipped         : {skipped_count}
Report          : {REPORT_FILE}
{'=' * 60}
"""
    print(summary)

    return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
