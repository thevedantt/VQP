"""
Persist blueprint lifecycle artifacts to disk (Phase 4.4).

Artifact layout under outputv2/diagram_runs/{paper_id}/{question_id}/:

  question.txt
  raw_blueprint.json
  evaluated_blueprint.json
  adapted_blueprint.json
  metadata.json
  final.svg
"""

import json
import shutil
from pathlib import Path

DIAGRAM_RUNS_DIR = (
    Path(__file__).resolve().parent.parent / "outputv2" / "diagram_runs"
)


def _save_json(data, directory, filename):
    path = directory / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


class BlueprintStore:

    def __init__(self, paper_id, question_id):
        self.run_dir = DIAGRAM_RUNS_DIR / paper_id / question_id

    def ensure_dir(self):
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def save_question(self, question_text):
        self.ensure_dir()
        (self.run_dir / "question.txt").write_text(
            question_text or "", encoding="utf-8"
        )

    def save_raw_blueprint(self, blueprint):
        self.ensure_dir()
        _save_json(blueprint, self.run_dir, "raw_blueprint.json")

    def save_evaluated_blueprint(self, blueprint):
        self.ensure_dir()
        _save_json(blueprint, self.run_dir, "evaluated_blueprint.json")

    def save_adapted_blueprint(self, blueprint):
        self.ensure_dir()
        _save_json(blueprint, self.run_dir, "adapted_blueprint.json")

    def save_metadata(self, metadata):
        self.ensure_dir()
        _save_json(metadata, self.run_dir, "metadata.json")

    def save_final_svg(self, svg_path):
        if not svg_path:
            return
        src = Path(svg_path)
        if src.exists():
            self.ensure_dir()
            shutil.copy2(src, self.run_dir / "final.svg")
