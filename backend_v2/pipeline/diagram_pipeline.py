"""
Unified single-diagram pipeline (Phase 4.2 — adapter layer).

Wraps the existing, working flow:

    Classifier -> Schema Router -> Blueprint Generator
    -> Blueprint Evaluator -> Adapter -> Compiler Router -> SVG

The adapter layer transforms backend blueprint format into the exact
format expected by each APPROCH2 compiler, preventing validation failure.
"""

import json
import re
import sys
import traceback
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
BACKEND_V2 = PIPELINE_DIR.parent
BASE = BACKEND_V2.parent

sys.path.insert(0, str(BACKEND_V2))
sys.path.insert(0, str(BASE))

for sub in ("ray", "circuit", "fbd", "magnetic_field", "semiconductor", "graph"):
    sys.path.insert(0, str(BASE / "approch2" / sub))

from diagram_intelligence.classifier.llm_classifier import DiagramClassifier
from diagram_intelligence.blueprint_generator.blueprint_generator import (
    BlueprintGenerator,
)
from diagram_intelligence.blueprint_evaluator import BlueprintEvaluator

from pipeline.logger import PipelineLogger

# ---------------------------------------------------------------------------
# Adapter imports (Phase 4.2)
# ---------------------------------------------------------------------------

from diagram_generation.adapters import (
    circuit_adapter,
    ray_adapter,
    fbd_adapter,
    magnetic_adapter,
    semiconductor_adapter,
    graph_adapter,
)

ADAPTERS = {
    "circuit": circuit_adapter.adapt,
    "ray": ray_adapter.adapt,
    "fbd": fbd_adapter.adapt,
    "magnetic": magnetic_adapter.adapt,
    "semiconductor": semiconductor_adapter.adapt,
    "graph": graph_adapter.adapt,
}

OUTPUTV2_DIR = BACKEND_V2 / "outputv2"
RAW_BLUEPRINT_DIR = OUTPUTV2_DIR / "raw_blueprints"
ENHANCED_BLUEPRINT_DIR = OUTPUTV2_DIR / "enhanced_blueprints"
EVALUATION_REPORT_DIR = OUTPUTV2_DIR / "evaluation_reports"
COMPILED_SVG_DIR = OUTPUTV2_DIR / "compiled_svgs"
SCHEMA_DIR = BACKEND_V2 / "schemas"

for d in (
    RAW_BLUEPRINT_DIR,
    ENHANCED_BLUEPRINT_DIR,
    EVALUATION_REPORT_DIR,
    COMPILED_SVG_DIR,
):
    d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Compilers (mirror diagram_intelligence/compiler_router.py)
# ---------------------------------------------------------------------------


def _compile_ray(blueprint, output_path):
    from approch2.ray.ray_compiler import RayCompiler

    adapted = ADAPTERS["ray"](blueprint)
    print(f"[ADAPTER] ray adapted blueprint: {json.dumps(adapted, indent=2)[:200]}...")
    RayCompiler().compile_to_file(adapted, str(output_path))


def _compile_circuit(blueprint, output_path):
    from approch2.circuit.circuit_compiler import CircuitCompiler
    from diagram_generation.compatibility.circuit_component_mapper import (
        CircuitRerouteError,
        apply_compatibility_fixes,
        check_blueprint_compatibility,
    )

    adapted = ADAPTERS["circuit"](blueprint)

    compatibility = check_blueprint_compatibility(adapted)
    if compatibility["needs_reroute"]:
        raise CircuitRerouteError(compatibility["unsupported"])
    if compatibility["aliased"]:
        print(f"[COMPATIBILITY] aliased components: {compatibility['aliased']}")
        adapted = apply_compatibility_fixes(adapted)

    print(f"[ADAPTER] circuit adapted blueprint: {json.dumps(adapted, indent=2)}...")
    result = CircuitCompiler().compile_to_file(adapted, str(output_path))

    if not result.get("success"):
        print("results")
        print(result)
        errors = "; ".join(result.get("errors", []))
        raise ValueError(f"Circuit compilation failed: {errors}")


def _compile_fbd(blueprint, output_path):
    from approch2.fbd.fbd_layout import generate_layout
    from approch2.fbd.fbd_renderer import render_svg

    adapted = ADAPTERS["fbd"](blueprint)
    print(f"[ADAPTER] fbd adapted blueprint: object_type={adapted.get('object_type')}")
    layout = generate_layout(adapted)
    svg = render_svg(layout)
    output_path.write_text(svg, encoding="utf-8")


def _compile_magnetic(blueprint, output_path):
    from approch2.magnetic_field.mf_layout import generate_layout
    from approch2.magnetic_field.mf_field_engine import generate_field
    from approch2.magnetic_field.mf_renderer import render_svg

    adapted = ADAPTERS["magnetic"](blueprint)
    print(f"[ADAPTER] magnetic adapted blueprint: object_type={adapted.get('object_type')}")
    layout = generate_layout(adapted)
    generate_field(adapted["object_type"])
    svg = render_svg(layout)
    output_path.write_text(svg, encoding="utf-8")


def _compile_semiconductor(blueprint, output_path):
    from approch2.semiconductor.semi_layout import generate_layout
    from approch2.semiconductor.semi_renderer import render_svg

    adapted = ADAPTERS["semiconductor"](blueprint)
    print(f"[ADAPTER] semiconductor adapted blueprint: object_type={adapted.get('object_type')}")
    layout = generate_layout(adapted)
    svg = render_svg(layout)
    output_path.write_text(svg, encoding="utf-8")


def _compile_graph(blueprint, output_path):
    from approch2.graph.graph_renderer import render_graph

    adapted = ADAPTERS["graph"](blueprint)
    print(f"[ADAPTER] graph adapted blueprint: object_type={adapted.get('object_type')}")
    render_graph(adapted["object_type"], output_path)


COMPILERS = {
    "ray": _compile_ray,
    "circuit": _compile_circuit,
    "fbd": _compile_fbd,
    "magnetic": _compile_magnetic,
    "semiconductor": _compile_semiconductor,
    "graph": _compile_graph,
}


# ---------------------------------------------------------------------------
# Output validation helpers
# ---------------------------------------------------------------------------


_SVG_DRAWABLE_RE = re.compile(
    r"<(path|line|circle|rect|polygon|polyline|text|ellipse|image)\b",
    re.IGNORECASE,
)


def _check_svg(output_path):
    """
    Validate that a compiled SVG exists, is non-empty, and actually
    contains drawable content. Raises on failure (Phase 4.8, Issue 3) -
    a renderer that "succeeds" but silently writes a blank canvas must be
    reported as a failure, not a false success.
    """
    path = Path(output_path)
    if not path.exists():
        raise FileNotFoundError(f"SVG file was not created: {output_path}")

    size = path.stat().st_size
    if size == 0:
        raise ValueError(f"SVG file is empty: {output_path}")

    content = path.read_text(encoding="utf-8", errors="ignore")
    if "<svg" not in content.lower():
        raise ValueError(f"File is not a valid SVG: {output_path}")
    if not _SVG_DRAWABLE_RE.search(content):
        raise ValueError(
            f"SVG contains no drawable elements (blank diagram): {output_path}"
        )

    print(f"[CHECK] SVG OK: {output_path} ({size} bytes)")
    return True


_SVG_REVISION_RE = re.compile(r"_v(\d+)\.svg$", re.IGNORECASE)


def resolve_compiled_svg(paper_id, question_id):
    """
    Find the current SVG for a question under the family-aware naming
    convention (Phase 4.8, Issue 4):

        {paper_id}_{question_id}_{family}.svg               (initial)
        {paper_id}_{question_id}_{family}_v{n}.svg           (revisions)

    Picks whichever file was written most recently. A revision number
    alone is not a reliable "latest" signal: re-running full diagram
    generation for this question (e.g. after editing the paper) writes
    a fresh unversioned file without touching old `_v{n}.svg` revision
    artifacts, and that fresh file must win even though it has no
    version suffix. Returns None if nothing matches.
    """
    candidates = list(COMPILED_SVG_DIR.glob(f"{paper_id}_{question_id}_*.svg"))
    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


# ---------------------------------------------------------------------------
# Adapted compile wrapper — used by both pipelines
# ---------------------------------------------------------------------------


def compile_and_check(family, blueprint, output_path):
    """
    Run the compiler for a family, applying the adapter layer first,
    then validating the output. Deletes any stale SVG before generation.
    """
    if family not in COMPILERS:
        raise ValueError(f"Unknown family: {family}")

    # Delete stale SVG if it exists (Task 7)
    out = Path(output_path)
    if out.exists():
        print(f"[CLEANUP] Deleting stale SVG: {out.name}")
        out.unlink()

    print(f"[COMPILE] family={family} output={output_path}")
    print(f"[COMPILE] raw blueprint: {json.dumps(blueprint, indent=2)[:300]}...")

    COMPILERS[family](blueprint, output_path)
    _check_svg(output_path)

    return str(output_path)


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------


def _load_schema(family):
    schema_file = SCHEMA_DIR / family / f"{family}_schema.json"
    if not schema_file.exists():
        return {}
    with open(schema_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_examples(family):
    examples_file = SCHEMA_DIR / family / "examples.json"
    if not examples_file.exists():
        return []
    with open(examples_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _merge_schema(blueprint, family):
    if not isinstance(blueprint, dict):
        return blueprint

    schema = _load_schema(family)
    if not isinstance(schema, dict) or not schema:
        return blueprint

    merged = schema.copy()
    merged.update(blueprint)

    for key in schema:
        if (
            isinstance(schema[key], dict)
            and key in blueprint
            and isinstance(blueprint[key], dict)
        ):
            merged[key] = {**schema[key], **blueprint[key]}

    return merged


def _save_json(data, directory, filename):
    path = directory / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def _normalize_blueprint(blueprint):
    """LLM may return a list (e.g. copied from an examples array)."""
    if isinstance(blueprint, list):
        if len(blueprint) == 1 and isinstance(blueprint[0], dict):
            blueprint = blueprint[0]
        elif len(blueprint) > 0 and isinstance(blueprint[0], dict):
            blueprint = blueprint[0].get("blueprint", blueprint[0])
    return blueprint


# ---------------------------------------------------------------------------
# Lazily-constructed, shared pipeline components
# ---------------------------------------------------------------------------

_classifier = None
_generator = None
_evaluator = None


def get_components():
    global _classifier, _generator, _evaluator

    if _classifier is None:
        _classifier = DiagramClassifier()
    if _generator is None:
        _generator = BlueprintGenerator()
    if _evaluator is None:
        _evaluator = BlueprintEvaluator()

    return _classifier, _generator, _evaluator


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_diagram(question, paper_id=None, question_id=None, logger=None, classification=None):
    """
    Run the full diagram pipeline for a single question.

    Classifier -> Schema Router -> Blueprint Generator
    -> Blueprint Evaluator -> Compiler Router -> SVG

    If `classification` is already known (e.g. the caller classified the
    question to decide whether a diagram is required at all), pass it in
    to avoid a redundant classifier call.

    Returns:
        {
            "question": str,
            "family": str | None,
            "svg_path": str | None,
            "status": "SUCCESS" | "SKIPPED" | "FAILED",
            "error": str | None,
        }
    """
    own_logger = logger is None
    if own_logger:
        logger = PipelineLogger()

    result = {
        "question": question,
        "family": None,
        "svg_path": None,
        "status": "FAILED",
        "error": None,
    }

    try:
        classifier, generator, evaluator = get_components()

        # ---- Step 1: Classify ----------------------------------------
        if classification is None:
            classification = classifier.classify(question)
            logger.log_classifier(question, classification)

        if not classification.get("diagram_required"):
            result["status"] = "SKIPPED"
            result["error"] = "No diagram required"
            return result

        family = classification.get("family", "").lower().strip()
        result["family"] = family

        if family not in COMPILERS:
            result["status"] = "FAILED"
            result["error"] = f"Unknown family: {family}"
            logger.log_error("SCHEMA ROUTER", result["error"])
            return result

        # ---- Step 2: Schema Router -------------------------------------
        schema_path = SCHEMA_DIR / family / f"{family}_schema.json"
        logger.log_schema_router(family, str(schema_path))

        schema = _load_schema(family)
        examples = _load_examples(family)

        # ---- Step 3: Blueprint Generator --------------------------------
        gen_result = generator.generate_blueprint(question, family)
        raw_blueprint = _normalize_blueprint(gen_result["blueprint"])

        if not isinstance(raw_blueprint, dict):
            result["status"] = "FAILED"
            result["error"] = (
                f"Blueprint is not a dict (got {type(raw_blueprint).__name__})"
            )
            logger.log_error("BLUEPRINT GENERATOR", result["error"])
            return result

        logger.log_blueprint_generator(raw_blueprint)

        base_id = _resolve_base_id(paper_id, question_id, raw_blueprint, family)

        _save_json(raw_blueprint, RAW_BLUEPRINT_DIR, f"{base_id}_raw.json")

        # ---- Step 4: Blueprint Evaluator --------------------------------
        evaluation = evaluator.evaluate(question, family, schema, raw_blueprint, examples)
        enhanced_blueprint = evaluation.get("enhanced_blueprint", raw_blueprint)

        logger.log_evaluator(
            evaluation.get("issues_found", []),
            evaluation.get("improvements", []),
        )

        _save_json(enhanced_blueprint, ENHANCED_BLUEPRINT_DIR, f"{base_id}_enhanced.json")
        _save_json(evaluation, EVALUATION_REPORT_DIR, f"{base_id}_evaluation.json")

        # ---- Step 5: Compiler Router + Adapter ---------------------------
        merged_blueprint = _merge_schema(enhanced_blueprint, family)

        svg_path = COMPILED_SVG_DIR / f"{base_id}.svg"
        compile_and_check(family, merged_blueprint, svg_path)

        logger.log_compiler(family, str(svg_path))

        result["status"] = "SUCCESS"
        result["svg_path"] = str(svg_path)
        return result

    except Exception as e:
        result["status"] = "FAILED"
        result["error"] = str(e)
        logger.log_error("DIAGRAM PIPELINE", f"{e}\n{traceback.format_exc()}")
        return result

    finally:
        if own_logger:
            logger.close()


def _resolve_base_id(paper_id, question_id, blueprint, family):
    """{paper_id}_{question_id}.svg naming rule, with sane fallbacks."""
    if paper_id and question_id:
        raw = f"{paper_id}_{question_id}"
    elif question_id:
        raw = question_id
    elif paper_id:
        raw = paper_id
    else:
        raw = blueprint.get("question_id") or f"{family}_output"

    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in str(raw))


def main():
    question = input("Question: ")
    result = generate_diagram(question)

    print()
    print("=" * 60)
    print("DIAGRAM PIPELINE RESULT")
    print("=" * 60)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
