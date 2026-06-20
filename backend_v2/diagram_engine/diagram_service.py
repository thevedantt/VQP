"""
Business layer — orchestrates the full diagram pipeline (Phase 4.4).

Responsibilities:
  1.  Classify question
  2.  Schema router
  3.  Blueprint generation (hybrid EXAMPLE_BASED / SCHEMA_BASED)
  4.  Blueprint evaluation
  5.  Adapter + Compiler
  6.  Store artifacts (including adapted blueprint)
  7.  Return result
"""

import sys
import json
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parent
BACKEND_V2 = SERVICE_DIR.parent
BASE = BACKEND_V2.parent

sys.path.insert(0, str(BACKEND_V2))
sys.path.insert(0, str(BASE))

for sub in ("ray", "circuit", "fbd", "magnetic_field", "semiconductor", "graph"):
    sys.path.insert(0, str(BASE / "approch2" / sub))

from diagram_generation.diagram_generation_pipeline import (
    generate_diagram_for_question,
    DIAGRAM_RUNS_DIR,
)
from pipeline.diagram_pipeline import (
    ADAPTERS,
    COMPILED_SVG_DIR,
    _save_json,
)
from diagram_engine.generation_manager import GenerationManager


def run(question, paper_id, question_id):
    """
    Orchestrate the full pipeline and return a clean result dict.

    The existing `generate_diagram_for_question` handles all core steps.
    This wrapper adds adapted-blueprint persistence and unified timing.

    Returns:
        {
            "question_id": str | None,
            "status": "SUCCESS" | "SKIPPED" | "FAILED",
            "family": str | None,
            "svg_path": str | None,
            "reason": str | None,
            "similarity_score": float | None,
            "generation_mode": "EXAMPLE_BASED" | "SCHEMA_BASED" | None,
            "confidence": int | None,
            "generation_time": float | None,
            "error": str | None,
        }
    """
    gm = GenerationManager(question_id=question_id)

    with gm:
        raw_result = generate_diagram_for_question(
            question,
            paper_id=paper_id,
            question_id=question_id,
        )

    status = raw_result.get("status")
    success = status == "SUCCESS"
    family = raw_result.get("family")
    error = raw_result.get("error")
    reason = raw_result.get("reason")
    # Prefer the evaluator-corrected blueprint - it's what actually
    # compiled into the SVG. Falling back to raw_blueprint would re-adapt
    # whatever issues the evaluator had already fixed (Phase 4.10 bugfix:
    # this used to always adapt raw_blueprint, so a later revision reading
    # adapted_blueprint.json as its starting point would resurrect a
    # non-canonical field value the renderer doesn't recognize).
    raw_blueprint = raw_result.get("raw_blueprint")
    enhanced_blueprint = raw_result.get("enhanced_blueprint") or raw_blueprint
    svg_filename = raw_result.get("svg_path")

    full_svg_path = None
    if success and svg_filename:
        full_svg_path = COMPILED_SVG_DIR / svg_filename
        gm.family = family

        # Save adapted blueprint (the one artifact the existing pipeline skips)
        adapted = ADAPTERS[family](enhanced_blueprint or {})
        _save_adapted_blueprint(adapted, paper_id, question_id)

    gm.family = family
    gm.print_report(svg_path=full_svg_path)

    return {
        "question_id": question_id,
        "status": status,
        "family": family,
        "svg_path": str(full_svg_path) if full_svg_path else None,
        "reason": reason,
        "similarity_score": raw_result.get("similarity_score"),
        "generation_mode": raw_result.get("generation_mode"),
        "confidence": raw_result.get("confidence"),
        "generation_time": gm.duration,
        "error": error,
    }


def _save_adapted_blueprint(adapted, paper_id, question_id):
    if not paper_id or not question_id:
        return
    run_dir = DIAGRAM_RUNS_DIR / paper_id / question_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _save_json(adapted, run_dir, "adapted_blueprint.json")
