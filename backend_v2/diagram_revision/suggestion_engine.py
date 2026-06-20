"""
AI improvement suggestions for a generated diagram (Phase 4.10, Issue 3).

Input:
  1. Question
  2. Blueprint (latest version)
  3. Evaluator report (from initial generation, if available)
  4. Compiler report (whether the SVG compiled and exists)

Output:
  3-5 short, concrete improvement suggestions, e.g.:
    "Add labels", "Increase spacing", "Show current direction"

These suggestions are surfaced in the "Improve Diagram" modal so a user
can accept one as-is, edit it, or write fully custom feedback before
submitting a revision.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

ENGINE_DIR = Path(__file__).resolve().parent
BACKEND_V2 = ENGINE_DIR.parent

sys.path.insert(0, str(BACKEND_V2))

load_dotenv(BACKEND_V2 / ".env")

from llm.gemini_retry import call_with_retry
from diagram_revision import revision_history as history

SUGGESTION_MODEL = "gemini-3.5-flash"

SYSTEM_PROMPT = """
You are a Physics Diagram Improvement Advisor.

Given a question, the current diagram blueprint, the evaluator's report
from generation, and the compiler status, suggest concrete improvements
a user could request next.

Output ONLY valid JSON in this format:

{
  "suggestions": [
    "Add labels",
    "Increase spacing",
    "Show current direction"
  ]
}

Rules:
- Return between 3 and 5 suggestions.
- Each suggestion must be short (2-6 words) and actionable.
- Be specific to this diagram family and question, not generic filler.
- Do NOT include markdown, notes, or explanations.
"""

FALLBACK_SUGGESTIONS = [
    "Add labels",
    "Increase spacing",
    "Improve readability",
]

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY2"))
    return _client


def _build_compiler_report(paper_id, question_id):
    from pipeline.diagram_pipeline import resolve_compiled_svg

    svg_path = resolve_compiled_svg(paper_id, question_id)
    if svg_path and Path(svg_path).exists():
        return {"compiled": True, "svg_path": str(svg_path)}
    return {"compiled": False, "svg_path": None}


def _build_prompt(question, family, blueprint, evaluation, compiler_report):
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

{json.dumps(blueprint, indent=2)}

====================================================
EVALUATOR REPORT
====================================================

{json.dumps(evaluation, indent=2) if evaluation else "(none available)"}

====================================================
COMPILER REPORT
====================================================

{json.dumps(compiler_report, indent=2)}

====================================================

Suggest 3-5 concrete improvements for this diagram.
"""


class SuggestionEngine:

    def generate_suggestions(self, paper_id, question_id):
        """
        Returns:
            {
                "success": bool,
                "suggestions": list[str],
                "error": str | None,
            }
        """
        blueprint = history.load_latest_blueprint(paper_id, question_id)
        if blueprint is None:
            return {
                "success": False,
                "suggestions": [],
                "error": (
                    f"No existing blueprint found for {paper_id}/{question_id}. "
                    "Generate the diagram first."
                ),
            }

        question = history.load_question(paper_id, question_id)
        evaluation = history.load_evaluation_report(paper_id, question_id)
        metadata = history.load_metadata(paper_id, question_id)
        family = (metadata or {}).get("family") or blueprint.get("family", "")
        compiler_report = _build_compiler_report(paper_id, question_id)

        try:
            suggestions = self._ask_llm(
                question, family, blueprint, evaluation, compiler_report
            )
        except Exception:
            suggestions = []

        if not suggestions:
            suggestions = FALLBACK_SUGGESTIONS

        return {"success": True, "suggestions": suggestions, "error": None}

    def _ask_llm(self, question, family, blueprint, evaluation, compiler_report):
        prompt = _build_prompt(question, family, blueprint, evaluation, compiler_report)

        response = call_with_retry(
            _get_client().models.generate_content,
            model=SUGGESTION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT.strip(),
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )

        content = response.text
        if not content:
            return []

        text = content.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return []

        suggestions = result.get("suggestions", [])
        if not isinstance(suggestions, list):
            return []

        return [s for s in suggestions if isinstance(s, str) and s.strip()][:5]
