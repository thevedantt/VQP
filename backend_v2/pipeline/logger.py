"""
Centralized logging for the VisualQ diagram/paper pipeline.

Every stage of the pipeline (classifier, schema router, blueprint
generator, evaluator, compiler, paper pipeline) writes a timestamped
block to both the console and a log file under outputv2/logs/.
"""

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path


BACKEND_V2 = Path(__file__).resolve().parent.parent
LOG_DIR = BACKEND_V2 / "outputv2" / "logs"


def _stringify(value):
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except TypeError:
        return str(value)


class PipelineLogger:

    def __init__(self, log_dir=None):
        self.log_dir = Path(log_dir) if log_dir else LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Second-granularity timestamp + a short random suffix: under
        # parallel diagram generation (Phase 4.8, Issue 5), multiple
        # loggers can otherwise be created within the same second and
        # collide on one file, interleaving unrelated questions' logs.
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.log"
        self.log_path = self.log_dir / filename

        self._fh = open(self.log_path, "a", encoding="utf-8")

    def _timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write(self, text):
        try:
            print(text)
        except UnicodeEncodeError:
            # Windows console codepages (e.g. cp1252) can't render every
            # unicode char a question might contain (superscripts, etc.) -
            # the log file below still gets the untouched UTF-8 text.
            encoding = sys.stdout.encoding or "utf-8"
            print(text.encode(encoding, errors="replace").decode(encoding))
        self._fh.write(text + "\n")
        self._fh.flush()

    def _block(self, title, fields):
        lines = [f"[{self._timestamp()}] [{title}]", ""]

        for label, value in fields.items():
            lines.append(f"{label}:")
            lines.append(_stringify(value))
            lines.append("")

        lines.append("---")
        self._write("\n".join(lines))

    def log_classifier(self, question, classifier_output):
        self._block("CLASSIFIER", {
            "Question": question,
            "Classifier Output": classifier_output,
        })

    def log_schema_router(self, family, schema_path):
        self._block("SCHEMA ROUTER", {
            "Family": family,
            "Schema Path": schema_path,
        })

    def log_blueprint_generator(self, blueprint):
        self._block("BLUEPRINT GENERATOR", {
            "Generated Blueprint": blueprint,
        })

    def log_example_retriever(self, family, similarity_score, best_match_question):
        self._block("EXAMPLE RETRIEVER", {
            "Family": family,
            "Similarity Score": similarity_score,
            "Best Match Question": best_match_question,
        })

    def log_blueprint_modifier(self, blueprint):
        self._block("BLUEPRINT MODIFIER", {
            "Modified Blueprint": blueprint,
        })

    def log_evaluator(self, issues_found, changes_made):
        self._block("EVALUATOR", {
            "Issues Found": issues_found,
            "Changes Made": changes_made,
        })

    def log_compiler(self, compiler_used, svg_path):
        self._block("COMPILER", {
            "Compiler Used": compiler_used,
            "SVG Path": svg_path,
        })

    def log_paper_pipeline(self, question_count, diagram_count, final_output):
        self._block("PAPER PIPELINE", {
            "Question Count": question_count,
            "Diagram Count": diagram_count,
            "Final Output": final_output,
        })

    def log_error(self, stage, message):
        self._block(f"ERROR ({stage})", {
            "Message": message,
        })

    def close(self):
        if not self._fh.closed:
            self._fh.close()
