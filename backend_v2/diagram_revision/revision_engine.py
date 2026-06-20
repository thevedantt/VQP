"""
Unified public API for diagram revision (Phase 4.6).

Flow:
  1. Load current blueprint (latest revision or initial)
  2. Process feedback into structured changes
  3. Gemini revises blueprint based on feedback
  4. Adapt + compile new SVG
  5. Save versioned artifacts
  6. Return result
"""

import json
import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from llm.gemini_retry import call_with_retry

ENGINE_DIR = Path(__file__).resolve().parent
BACKEND_V2 = ENGINE_DIR.parent
BASE = BACKEND_V2.parent

sys.path.insert(0, str(BACKEND_V2))
sys.path.insert(0, str(BASE))

for sub in ("ray", "circuit", "fbd", "magnetic_field", "semiconductor", "graph"):
    sys.path.insert(0, str(BASE / "approch2" / sub))

load_dotenv(BACKEND_V2 / ".env")

from pipeline.diagram_pipeline import (
    COMPILED_SVG_DIR,
    COMPILERS,
    _merge_schema,
    _check_svg,
)
from pipeline.logger import PipelineLogger

from diagram_revision import revision_history as history
from diagram_revision.feedback_processor import FeedbackProcessor

REVISION_MODEL = "gemini-3.5-flash"

REVISION_SYSTEM_PROMPT = """
You are a Physics Diagram Blueprint Reviser.

You are given:
1. The original question
2. The current blueprint (which already works)
3. User feedback describing what to improve

Your job is to MODIFY the existing blueprint to address the feedback.
Do NOT create a new blueprint from scratch — start with the current
blueprint and only change what the feedback asks for.

RULES:
1. Preserve the exact schema structure — do not add or remove keys.
2. Only change values that directly relate to the feedback.
3. Never remove required fields.
4. If the feedback is unclear or cannot be addressed, return the original blueprint unchanged.
5. Return ONLY valid JSON, no markdown, no explanation.

Format:
{
  "blueprint": { ... }
}
"""


class RevisionEngine:

    def __init__(self):
        self.feedback_processor = FeedbackProcessor()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY2"))

    def revise_diagram(self, paper_id, question_id, feedback, selected_suggestions=None):
        """
        Revise an existing diagram based on user feedback.

        Args:
            paper_id:   e.g. "PAPER001"
            question_id:  e.g. "Q07"
            feedback:   Free-text custom instructions (may be empty)
            selected_suggestions: AI suggestions the user ticked - these are
                already concrete, actionable change descriptions, so they're
                used directly as requested changes rather than re-interpreted
                by the feedback processor.

        Returns:
            {
                "success": bool,
                "revision_number": int,
                "svg_path": str | None,
                "changes": list[str],
                "error": str | None,
            }
        """
        logger = PipelineLogger()

        result = {
            "success": False,
            "revision_number": 0,
            "svg_path": None,
            "changes": [],
            "error": None,
        }

        selected_suggestions = [s.strip() for s in (selected_suggestions or []) if s and s.strip()]
        feedback = feedback or ""

        if not selected_suggestions and not feedback.strip():
            result["error"] = "No feedback or suggestions provided."
            return result

        try:
            # ---- Step 0: Determine revision number -------------------------
            rev = history.current_revision(paper_id, question_id) + 1
            result["revision_number"] = rev

            # ---- Step 1: Load current blueprint ----------------------------
            current_bp = history.load_latest_blueprint(paper_id, question_id)
            if current_bp is None:
                result["error"] = (
                    f"No existing blueprint found for {paper_id}/{question_id}. "
                    "Generate the diagram first."
                )
                logger.log_error("REVISION ENGINE", result["error"])
                return result

            family = self._resolve_family(paper_id, question_id, current_bp)

            if family not in COMPILERS:
                result["error"] = f"Unknown family: {family}"
                logger.log_error("REVISION ENGINE", result["error"])
                return result

            # Guard against a previous revision having drifted to a
            # different family's blueprint shape (e.g. an LLM turning a
            # semiconductor blueprint into a circuit one while "revising"
            # it - the compiler then gets a blueprint with none of the
            # fields it expects, producing a blank SVG). If the loaded
            # blueprint's own family tag doesn't match the resolved
            # family, it's not safe to revise further - recover from the
            # original pre-revision blueprint instead.
            loaded_family = (
                current_bp.get("family") or current_bp.get("diagram_family") or ""
            ).lower().strip()
            if loaded_family and loaded_family != family:
                logger.log_error(
                    "REVISION ENGINE",
                    f"Latest blueprint for {question_id} is tagged "
                    f"'{loaded_family}' but should be '{family}' - revision "
                    "history has drifted. Recovering from the original "
                    "generated blueprint instead.",
                )
                current_bp = history.load_initial_blueprint(paper_id, question_id)
                if current_bp is None:
                    result["error"] = (
                        f"Blueprint family drifted to '{loaded_family}' and no "
                        "original blueprint is available to recover from."
                    )
                    return result

            question = history.load_question(paper_id, question_id)

            # ---- Step 2: Build the change list ------------------------------
            # Ticked suggestions are already concrete and actionable - use
            # them as-is. Only run the feedback processor on free-text
            # manual instructions, which need interpretation.
            changes = list(selected_suggestions)
            if feedback.strip():
                processed = self.feedback_processor.process(question, family, feedback)
                changes += processed.get("requested_changes", [])
            result["changes"] = changes

            combined_feedback = "\n".join(f"- {s}" for s in selected_suggestions)
            if feedback.strip():
                combined_feedback = (
                    f"{combined_feedback}\n{feedback.strip()}" if combined_feedback else feedback.strip()
                )

            # Save feedback
            history.save_feedback(combined_feedback, paper_id, question_id, rev)

            print()
            print("=" * 60)
            print(f"[DIAGRAM REVISION]")
            print(f"  Question:    {question_id}")
            print(f"  Revision:    {rev}")
            print(f"  Feedback:    {combined_feedback}")
            print(f"  Changes:     {changes if changes else '(none parsed)'}")
            print("=" * 60)
            print()

            # ---- Step 3: Gemini revises blueprint ---------------------------
            revised_blueprint = self._revise_blueprint(
                question, family, current_bp, combined_feedback, changes
            )

            # Save revised blueprint
            history.save_blueprint(revised_blueprint, paper_id, question_id, rev)

            # ---- Step 4: Adapt + compile -----------------------------------
            merged = _merge_schema(revised_blueprint, family)
            # Family-aware, version-suffixed naming (Phase 4.8, Issue 4):
            # each revision gets its own self-describing filename, e.g.
            # PAPER001_Q07_circuit_v1.svg, PAPER001_Q07_circuit_v2.svg -
            # no overwriting, no stale-file cleanup needed.
            svg_filename = f"{paper_id}_{question_id}_{family}_v{rev}.svg"
            svg_path = COMPILED_SVG_DIR / svg_filename

            print(f"[COMPILE] family={family} output={svg_path}")
            print(
                f"[COMPILE] revised blueprint: "
                f"{json.dumps(revised_blueprint, indent=2)[:300]}..."
            )

            COMPILERS[family](merged, svg_path)
            _check_svg(svg_path)

            history.save_svg(svg_path, paper_id, question_id, rev)

            print(f"[REVISION] SVG saved: {svg_path}")

            result["success"] = True
            result["svg_path"] = str(svg_path)
            return result

        except Exception as e:
            result["error"] = str(e)
            logger.log_error("REVISION ENGINE", f"{e}\n{traceback.format_exc()}")
            return result

        finally:
            logger.close()

    # -------------------------------------------------------------------
    # Gemini blueprint revision
    # -------------------------------------------------------------------

    def _build_revision_prompt(self, question, family, current_blueprint, feedback, changes):
        changes_text = ""
        if changes:
            changes_text = "\n".join(f"- {c}" for c in changes)

        return f"""
====================================================
QUESTION
====================================================

{question}

====================================================
FAMILY
====================================================

{family}

====================================================
CURRENT BLUEPRINT
====================================================

{json.dumps(current_blueprint, indent=2)}

====================================================
FEEDBACK
====================================================

{feedback}

====================================================
REQUESTED CHANGES
====================================================

{changes_text or "(interpret from feedback above)"}

====================================================

Modify the CURRENT BLUEPRINT to address the feedback.
Return ONLY:

{{
  "blueprint": {{ ... }}
}}
"""

    def _revise_blueprint(self, question, family, current_blueprint, feedback, changes):
        prompt = self._build_revision_prompt(
            question, family, current_blueprint, feedback, changes
        )

        response = call_with_retry(
            self.client.models.generate_content,
            model=REVISION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=REVISION_SYSTEM_PROMPT.strip(),
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        content = response.text
        if not content:
            return current_blueprint

        text = content.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return current_blueprint

        return result.get("blueprint", current_blueprint)

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _resolve_family(self, paper_id, question_id, blueprint):
        """Determine the diagram family, preferring metadata.json (set once
        at initial generation) since the blueprint's own family-like keys
        can drift across LLM-driven revisions."""
        metadata = history.load_metadata(paper_id, question_id)
        if metadata and metadata.get("family"):
            return metadata["family"].lower().strip()

        family = blueprint.get("family") or blueprint.get("diagram_family", "")
        if not family:
            family = blueprint.get("renderer_type", "")
        return family.lower().strip()
