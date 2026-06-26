"""
Diagram generation pipeline (Phase 4, Module 6 — upgraded Phase 4.1).

Hybrid generation modes:

    Mode A — EXAMPLE_BASED  (similarity >= SIMILARITY_THRESHOLD)
        Question -> Retrieve Example -> Modify Blueprint -> Evaluate -> Compile

    Mode B — SCHEMA_BASED   (similarity < SIMILARITY_THRESHOLD)
        Question -> Schema -> Generate Blueprint From Schema -> Evaluate -> Compile

Family validation prevents family mismatch. Confidence scores blend retrieval
quality, evaluation quality, and family-match signals. Every run is traceable
under outputv2/diagram_runs/{paper_id}/{question_id}/.
"""

import json
import shutil
import sys
import time
import traceback
from pathlib import Path

DIAGRAM_GEN_DIR = Path(__file__).resolve().parent
BACKEND_V2 = DIAGRAM_GEN_DIR.parent
BASE = BACKEND_V2.parent

sys.path.insert(0, str(BACKEND_V2))
sys.path.insert(0, str(BASE))

from diagram_intelligence.classifier.llm_classifier import DiagramClassifier
from llm.gemini_evaluator import GeminiEvaluator

from pipeline.diagram_pipeline import (
    COMPILED_SVG_DIR,
    COMPILERS,
    ENHANCED_BLUEPRINT_DIR,
    EVALUATION_REPORT_DIR,
    RAW_BLUEPRINT_DIR,
    _SVG_REVISION_RE,
    _load_examples,
    _load_schema,
    _merge_schema,
    _normalize_blueprint,
    _resolve_base_id,
    _save_json,
    compile_and_check,
)
from pipeline.logger import PipelineLogger

from diagram_generation.diagram_explainer import explain
from diagram_generation.example_retriever import retrieve
from diagram_generation.blueprint_modifier import BlueprintModifier
from diagram_generation.schema_blueprint_generator import SchemaBlueprintGenerator
from diagram_generation.family_validator import validate as validate_family
from diagram_generation.diagram_scanner import scan_paper

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIMILARITY_THRESHOLD = 0.85

# Phase 4.9, Task C: below this floor, a retrieved "best match" isn't a real
# match (observed retrievals around 0.20-0.30 against unrelated examples) -
# never route generation through it, always fall back to SCHEMA_BASED.
MIN_SIMILARITY_FOR_RETRIEVAL = 0.50

DIAGRAM_RUNS_DIR = BACKEND_V2 / "outputv2" / "diagram_runs"

# ---------------------------------------------------------------------------
# Lazily-constructed, shared pipeline components
# ---------------------------------------------------------------------------

_classifier = None
_modifier = None
_schema_generator = None
_evaluator = None


def get_components():
    global _classifier, _modifier, _schema_generator, _evaluator

    if _classifier is None:
        _classifier = DiagramClassifier()
    if _modifier is None:
        _modifier = BlueprintModifier()
    if _schema_generator is None:
        _schema_generator = SchemaBlueprintGenerator()
    if _evaluator is None:
        _evaluator = GeminiEvaluator()

    return _classifier, _modifier, _schema_generator, _evaluator


# ---------------------------------------------------------------------------
# Confidence helpers
# ---------------------------------------------------------------------------


def _evaluation_score(evaluation):
    issues = evaluation.get("issues", [])
    n = len(issues)
    if n == 0:
        return 100
    if n <= 2:
        return 80
    if n <= 4:
        return 60
    return 40


def _compute_confidence(similarity_score, evaluation, family_valid, generation_mode):
    eval_score = _evaluation_score(evaluation)
    fam_score = 100 if family_valid else 0

    if generation_mode == "EXAMPLE_BASED":
        retrieval_contrib = min(similarity_score * 100, 70) * 0.3
    else:
        retrieval_contrib = 20.0

    evaluation_contrib = eval_score * 0.5
    family_contrib = fam_score * 0.2

    return round(retrieval_contrib + evaluation_contrib + family_contrib)


# ---------------------------------------------------------------------------
# Generation metrics (Phase 4.8, Issue 6)
# ---------------------------------------------------------------------------


def _print_timing_report(question_id, timing):
    print()
    print(f"[METRICS] {question_id or '?'}")
    if timing.get("generation_seconds") is not None:
        print(f"  Generation:   {timing['generation_seconds']} sec")
    if timing.get("evaluation_seconds") is not None:
        print(f"  Evaluation:   {timing['evaluation_seconds']} sec")
    if timing.get("compilation_seconds") is not None:
        print(f"  Compilation:  {timing['compilation_seconds']} sec")
    print(f"  Total:        {timing.get('total_seconds')} sec")


# ---------------------------------------------------------------------------
# Traceability
# ---------------------------------------------------------------------------


def _save_run_artifacts(
    paper_id,
    question_id,
    question_text,
    retrieval,
    raw_blueprint,
    evaluation,
    svg_path,
    metadata,
):
    if not paper_id or not question_id:
        return

    run_dir = DIAGRAM_RUNS_DIR / paper_id / question_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # question.txt
    (run_dir / "question.txt").write_text(question_text or "", encoding="utf-8")

    # retrieved_example.json (may be None for SCHEMA_BASED)
    if retrieval and retrieval.get("best_match"):
        _save_json(retrieval["best_match"], run_dir, "retrieved_example.json")

    # generated_blueprint.json
    _save_json(raw_blueprint, run_dir, "generated_blueprint.json")

    # evaluation_report.json
    _save_json(evaluation, run_dir, "evaluation_report.json")

    # final.svg (copy from compiled_svgs)
    if svg_path and Path(svg_path).exists():
        shutil.copy2(svg_path, run_dir / "final.svg")

    # metadata.json
    _save_json(metadata, run_dir, "metadata.json")


# ---------------------------------------------------------------------------
# Single-question pipeline
# ---------------------------------------------------------------------------


def generate_diagram_for_question(question, paper_id=None, question_id=None, logger=None):
    """
    Returns:
        {
            "question_id": str | None,
            "family": str | None,
            "reason": str | None,
            "similarity_score": float | None,
            "generation_mode": "EXAMPLE_BASED" | "SCHEMA_BASED" | None,
            "retrieved_example_rank": int | None,
            "top_5_similarities": [float, ...] | None,
            "confidence": int | None,
            "status": "SUCCESS" | "SKIPPED" | "FAILED",
            "svg_path": str | None,
            "error": str | None,
        }
    """
    own_logger = logger is None
    if own_logger:
        logger = PipelineLogger()

    result = {
        "question_id": question_id,
        "family": None,
        "reason": None,
        "similarity_score": None,
        "generation_mode": None,
        "retrieved_example_rank": None,
        "top_5_similarities": None,
        "confidence": None,
        "status": "FAILED",
        "svg_path": None,
        "error": None,
        "raw_blueprint": None,
        "enhanced_blueprint": None,
        "timing": {
            "generation_seconds": None,
            "evaluation_seconds": None,
            "compilation_seconds": None,
            "total_seconds": None,
        },
    }

    raw_blueprint = None
    retrieval = None
    evaluation = None
    svg_filename = None
    family_valid_result = None
    t_start = time.perf_counter()

    try:
        classifier, modifier, schema_generator, evaluator = get_components()

        # ---- Step 1: Classify ------------------------------------------
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

        # ---- Step 1b: Family Validation (Task 4) -----------------------
        # Phase 4.8, Issue 2: a mismatch with a known-good expected family
        # (e.g. classifier said "circuit" for a PN-junction/diode question)
        # is auto-corrected to the keyword-suggested family rather than
        # failing the question outright.
        family_valid_result = validate_family(question, family)
        if not family_valid_result["valid"]:
            expected_family = family_valid_result.get("expected_family")
            if expected_family and expected_family in COMPILERS:
                logger.log_error(
                    "FAMILY VALIDATOR",
                    f"{family_valid_result['reason']} -> auto-corrected to "
                    f"'{expected_family}'",
                )
                family = expected_family
                result["family"] = family
            else:
                result["status"] = "FAILED"
                result["error"] = family_valid_result["reason"]
                logger.log_error("FAMILY VALIDATOR", result["error"])
                return result

        # ---- Step 1c: Question-specific Explanation (Task 3) -----------
        result["reason"] = explain(question, family)["reason"]

        # ---- Step 2: Schema Router --------------------------------------
        schema_path = BACKEND_V2 / "schemas" / family / f"{family}_schema.json"
        logger.log_schema_router(family, str(schema_path))

        schema = _load_schema(family)
        examples = _load_examples(family)

        # ---- Step 3: Example Retriever -----------------------------------
        retrieval = retrieve(question, family)
        best_match = retrieval["best_match"]
        example_blueprint = best_match.get("blueprint", best_match)
        similarity_score = retrieval["similarity_score"]
        result["similarity_score"] = similarity_score

        logger.log_example_retriever(
            family,
            similarity_score,
            best_match.get("question") or best_match.get("question_id"),
        )

        # ---- Step 4: Hybrid Generation (Task 1; gated by Task C) --------
        t_gen_start = time.perf_counter()
        if similarity_score < MIN_SIMILARITY_FOR_RETRIEVAL:
            mode = "SCHEMA_BASED"
            gen_result = schema_generator.generate_blueprint(question, family, schema)
            raw_blueprint = _normalize_blueprint(gen_result.get("blueprint"))
        elif similarity_score >= SIMILARITY_THRESHOLD:
            mode = "EXAMPLE_BASED"
            modifier_result = modifier.modify_blueprint(
                question, family, schema, example_blueprint
            )
            raw_blueprint = _normalize_blueprint(modifier_result.get("blueprint"))
        else:
            mode = "SCHEMA_BASED"
            gen_result = schema_generator.generate_blueprint(question, family, schema)
            raw_blueprint = _normalize_blueprint(gen_result.get("blueprint"))
        result["timing"]["generation_seconds"] = round(time.perf_counter() - t_gen_start, 1)

        result["generation_mode"] = mode

        if not isinstance(raw_blueprint, dict):
            result["status"] = "FAILED"
            result["error"] = (
                f"Blueprint is not a dict (got {type(raw_blueprint).__name__})"
            )
            logger.log_error("BLUEPRINT GENERATION", result["error"])
            return result

        if mode == "EXAMPLE_BASED":
            logger.log_blueprint_modifier(raw_blueprint)
        else:
            logger.log_blueprint_generator(raw_blueprint)

        base_id = _resolve_base_id(paper_id, question_id, raw_blueprint, family)
        _save_json(raw_blueprint, RAW_BLUEPRINT_DIR, f"{base_id}_raw.json")

        # ---- Step 5: Blueprint Evaluator -----------------------------------
        t_eval_start = time.perf_counter()
        evaluation = evaluator.evaluate(question, family, schema, raw_blueprint, examples)
        result["timing"]["evaluation_seconds"] = round(time.perf_counter() - t_eval_start, 1)
        enhanced_blueprint = evaluation.get("corrected_blueprint", raw_blueprint)

        logger.log_evaluator(
            evaluation.get("issues", []),
            evaluation.get("changes", []),
        )

        _save_json(enhanced_blueprint, ENHANCED_BLUEPRINT_DIR, f"{base_id}_enhanced.json")
        _save_json(evaluation, EVALUATION_REPORT_DIR, f"{base_id}_evaluation.json")

        # ---- Step 5b: Confidence Score (Task 5) ---------------------------
        family_valid = family_valid_result.get("valid", True) if family_valid_result else True
        confidence = _compute_confidence(
            similarity_score, evaluation, family_valid, mode
        )
        result["confidence"] = confidence

        # ---- Step 6: Compiler Router + Adapter + Validation --------------
        merged_blueprint = _merge_schema(enhanced_blueprint, family)

        # Family-aware naming (Phase 4.8, Issue 4): self-describing
        # filenames, e.g. PAPER001_Q07_circuit.svg, PAPER001_Q09_ray.svg.
        # Clean up any stale unversioned SVG left over from a prior run
        # under a different family (e.g. a misclassification fix) - never
        # touch versioned `_v{n}.svg` revision files, those belong to the
        # revision engine.
        svg_filename = f"{base_id}_{family}.svg"
        svg_path = COMPILED_SVG_DIR / svg_filename
        if paper_id and question_id:
            for stale in COMPILED_SVG_DIR.glob(f"{paper_id}_{question_id}_*.svg"):
                if stale.name != svg_filename and not _SVG_REVISION_RE.search(stale.name):
                    stale.unlink()

        t_compile_start = time.perf_counter()
        compile_and_check(family, merged_blueprint, svg_path)
        result["timing"]["compilation_seconds"] = round(time.perf_counter() - t_compile_start, 1)

        logger.log_compiler(family, str(svg_path))

        # ---- Step 7: Traceability (Tasks 9, 10; Phase 4.9 Task B/E) -----
        result["retrieved_example_rank"] = retrieval.get("rank")
        result["top_5_similarities"] = retrieval.get("top_5_similarities")

        metadata = {
            "paper_id": paper_id,
            "question_id": question_id,
            "family": family,
            "generation_mode": mode,
            "similarity_score": similarity_score,
            "retrieved_example_rank": retrieval.get("rank"),
            "top_5_similarities": retrieval.get("top_5_similarities"),
            "confidence": confidence,
            "reason": result["reason"],
            "future_revision_ready": True,
        }
        # Phase 4.9, Task C: only persist the retrieved example as a real
        # match when it was actually used (EXAMPLE_BASED) - below the
        # similarity floor it's noise, not a usable reference.
        retrieval_for_artifacts = retrieval if mode == "EXAMPLE_BASED" else None
        _save_run_artifacts(
            paper_id,
            question_id,
            question,
            retrieval_for_artifacts,
            raw_blueprint,
            evaluation,
            str(svg_path),
            metadata,
        )

        result["timing"]["total_seconds"] = round(time.perf_counter() - t_start, 1)
        _print_timing_report(question_id, result["timing"])

        result["status"] = "SUCCESS"
        result["svg_path"] = svg_filename
        result["raw_blueprint"] = raw_blueprint
        result["enhanced_blueprint"] = enhanced_blueprint
        return result

    except Exception as e:
        result["timing"]["total_seconds"] = round(time.perf_counter() - t_start, 1)
        _print_timing_report(question_id, result["timing"])

        result["status"] = "FAILED"
        result["error"] = str(e)
        logger.log_error("DIAGRAM GENERATION PIPELINE", f"{e}\n{traceback.format_exc()}")

        # Save partial artifacts even on failure
        metadata = {
            "paper_id": paper_id,
            "question_id": question_id,
            "family": result.get("family"),
            "generation_mode": result.get("generation_mode"),
            "similarity_score": result.get("similarity_score"),
            "retrieved_example_rank": result.get("retrieved_example_rank"),
            "top_5_similarities": result.get("top_5_similarities"),
            "confidence": result.get("confidence"),
            "reason": result.get("reason"),
            "error": str(e),
            "future_revision_ready": True,
        }
        _save_run_artifacts(
            paper_id,
            question_id,
            question,
            retrieval,
            raw_blueprint,
            evaluation,
            None,
            metadata,
        )
        return result

    finally:
        if own_logger:
            logger.close()


# ---------------------------------------------------------------------------
# Whole-paper pipeline
# ---------------------------------------------------------------------------


def generate_all_for_paper(paper_id):
    """
    Returns:
        {
            "paper_id": str,
            "generated": int,
            "failed": int,
            "svg_files": [str, ...],
            "results": [ ...generate_diagram_for_question() output... ],
        }
    """
    logger = PipelineLogger()

    try:
        scan = scan_paper(paper_id)

        results = []
        for entry in scan["diagram_questions"]:
            result = generate_diagram_for_question(
                entry["question"],
                paper_id=paper_id,
                question_id=entry["question_id"],
                logger=logger,
            )
            results.append(result)

        generated = sum(1 for r in results if r["status"] == "SUCCESS")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        svg_files = [r["svg_path"] for r in results if r["svg_path"]]

        _print_report(paper_id, results, generated, failed)

        return {
            "paper_id": paper_id,
            "generated": generated,
            "failed": failed,
            "svg_files": svg_files,
            "results": results,
        }

    finally:
        logger.close()


def _print_report(paper_id, results, generated, failed):
    print()
    print("=" * 60)
    print("DIAGRAM GENERATION REPORT")
    print("=" * 60)
    print()
    print(f"Paper: {paper_id}")

    for r in results:
        print()
        print("-" * 60)
        print(f"{r['question_id']}")
        print()
        print(f"Family: {r['family']}")
        print(f"Mode: {r['generation_mode']}")
        print(f"Similarity: {r['similarity_score']}")
        print(f"Retrieved Example Rank: {r.get('retrieved_example_rank')}")
        print(f"Top 5 Similarities: {r.get('top_5_similarities')}")
        print(f"Confidence: {r['confidence']}")
        print(f"Reason: {r['reason']}")
        print(f"Status: {r['status']}")
        if r["svg_path"]:
            print(f"SVG: {r['svg_path']}")
        if r["error"]:
            print(f"Error: {r['error']}")

    print()
    print("=" * 60)
    print("SUMMARY")
    print()
    print(f"Diagram Questions: {len(results)}")
    print(f"Generated: {generated}")
    print(f"Failed: {failed}")
    print("=" * 60)


def main():
    paper_id = input("Paper ID: ")

    result = generate_all_for_paper(paper_id)

    print()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
