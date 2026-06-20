"""
Maintain versioned history of diagram revisions (Phase 4.5).

Artifact layout under outputv2/diagram_runs/{paper_id}/{question_id}/:

  blueprint_v1.json      (initial generated blueprint)
  svg_v1.svg             (initial compiled SVG)
  feedback_1.txt         (feedback that led to v2)
  blueprint_v2.json
  svg_v2.svg
  feedback_2.txt
  ...
"""

import json
import re
import shutil
from pathlib import Path

DIAGRAM_RUNS_DIR = (
    Path(__file__).resolve().parent.parent / "outputv2" / "diagram_runs"
)


def _run_dir(paper_id, question_id):
    return DIAGRAM_RUNS_DIR / paper_id / question_id


def current_revision(paper_id, question_id):
    """Return the highest existing revision number, or 0 if none."""
    run_dir = _run_dir(paper_id, question_id)
    if not run_dir.exists():
        return 0
    max_n = 0
    for p in run_dir.iterdir():
        m = re.match(r"blueprint_v(\d+)\.json", p.name)
        if m:
            n = int(m.group(1))
            if n > max_n:
                max_n = n
    return max_n


def _save_json(data, directory, filename):
    path = directory / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def save_blueprint(blueprint, paper_id, question_id, revision):
    run_dir = _run_dir(paper_id, question_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    return _save_json(blueprint, run_dir, f"blueprint_v{revision}.json")


def save_svg(svg_path, paper_id, question_id, revision):
    run_dir = _run_dir(paper_id, question_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    src = Path(svg_path)
    if src.exists():
        dst = run_dir / f"svg_v{revision}.svg"
        shutil.copy2(src, dst)
        return str(dst)


def save_feedback(feedback, paper_id, question_id, revision):
    run_dir = _run_dir(paper_id, question_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"feedback_{revision}.txt"
    path.write_text(feedback or "", encoding="utf-8")
    return str(path)


def load_question(paper_id, question_id):
    """Load question text from stored artifacts."""
    from diagram_generation.diagram_generation_pipeline import DIAGRAM_RUNS_DIR
    q_path = DIAGRAM_RUNS_DIR / paper_id / question_id / "question.txt"
    if q_path.exists():
        return q_path.read_text(encoding="utf-8").strip()
    return ""


def load_latest_blueprint(paper_id, question_id):
    """Load the most recent blueprint: latest revision if any, else the
    initial generated_blueprint.json or adapted_blueprint.json."""
    rev = current_revision(paper_id, question_id)

    if rev > 0:
        bp_path = _run_dir(paper_id, question_id) / f"blueprint_v{rev}.json"
        if bp_path.exists():
            with open(bp_path, "r", encoding="utf-8") as f:
                return json.load(f)

    from diagram_generation.diagram_generation_pipeline import DIAGRAM_RUNS_DIR
    for name in ("generated_blueprint.json", "adapted_blueprint.json"):
        fallback = DIAGRAM_RUNS_DIR / paper_id / question_id / name
        if fallback.exists():
            with open(fallback, "r", encoding="utf-8") as f:
                return json.load(f)

    return None


def load_evaluation_report(paper_id, question_id):
    """Load the evaluator's report for the initial generation, if present."""
    eval_path = _run_dir(paper_id, question_id) / "evaluation_report.json"
    if eval_path.exists():
        with open(eval_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_metadata(paper_id, question_id):
    """Load run metadata.json (carries the reliably-tagged family), if present."""
    meta_path = _run_dir(paper_id, question_id) / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def list_versions(paper_id, question_id):
    """Return a sorted list of version dicts with available artifacts."""
    run_dir = _run_dir(paper_id, question_id)
    if not run_dir.exists():
        return []

    versions = {}
    for p in run_dir.iterdir():
        m = re.match(r"(blueprint|svg)_v(\d+)\.(json|svg)", p.name)
        if m:
            artifact = m.group(1)
            n = int(m.group(2))
            versions.setdefault(n, {"revision": n, "blueprint": None, "svg": None})
            if artifact == "blueprint":
                versions[n]["blueprint"] = str(p)
            elif artifact == "svg":
                versions[n]["svg"] = str(p)
        m2 = re.match(r"feedback_(\d+)\.txt", p.name)
        if m2:
            n = int(m2.group(1))
            versions.setdefault(n, {"revision": n, "blueprint": None, "svg": None})
            versions[n]["feedback"] = str(p)

    return [versions[k] for k in sorted(versions)]
