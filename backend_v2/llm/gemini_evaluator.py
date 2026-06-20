"""
Gemini-based blueprint evaluator (Phase 4.5).

Replaces the Qwen/OpenRouter evaluator. Reviews a generated blueprint
against the question, family, and schema, and returns issues, requested
changes, and a corrected blueprint. Never regenerates from scratch.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from llm.gemini_retry import call_with_retry

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

EVALUATOR_MODEL = "gemini-3.5-flash"

SYSTEM_PROMPT = """
You are a Physics Diagram Reviewer.

Your job is NOT to regenerate the blueprint from scratch.

Compare:
1. Question
2. Family
3. Schema
4. Generated Blueprint
5. Example Blueprints

Check for:
- Physics validation errors
- Missing labels
- Missing rays (ray-family diagrams)
- Missing circuit components (circuit-family diagrams)
- Question quality issues (blueprint not matching the question)

RULES:
1. Never remove required fields.
2. Never change schema structure.
3. Never invent unsupported renderer fields.
4. Only correct or improve the blueprint.
5. If no issues are found, return the original blueprint as corrected_blueprint.
6. Return JSON only. No markdown. No explanations. No code fences.

Format:
{
  "issues": [],
  "changes": [],
  "corrected_blueprint": { ... }
}
"""


class GeminiEvaluator:

    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def build_prompt(self, question, family, schema, blueprint, examples=None):
        examples_text = ""
        if examples:
            examples_text = (
                "\n====================================================\n"
                "EXAMPLE BLUEPRINTS\n"
                "====================================================\n\n"
                f"{json.dumps(examples, indent=2)}\n"
            )

        return f"""
====================================================
BLUEPRINT REVIEW TASK
====================================================

QUESTION

{question}

====================================================

FAMILY

{family}

====================================================

SCHEMA

{json.dumps(schema, indent=2)}

{examples_text}
====================================================

GENERATED BLUEPRINT

{json.dumps(blueprint, indent=2)}

====================================================

Return ONLY valid JSON in this format:

{{
  "issues": [],
  "changes": [],
  "corrected_blueprint": {{ ... }}
}}
"""

    def evaluate(self, question, family, schema, blueprint, examples=None):
        prompt = self.build_prompt(question, family, schema, blueprint, examples)

        response = call_with_retry(
            self.client.models.generate_content,
            model=EVALUATOR_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT.strip(),
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        content = response.text

        if not content:
            return {
                "issues": [
                    "Evaluator returned an empty response - using the unmodified blueprint."
                ],
                "changes": [],
                "corrected_blueprint": blueprint,
            }

        text = content.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return {
                "issues": [
                    "Evaluator response was not valid JSON - using the unmodified blueprint."
                ],
                "changes": [],
                "corrected_blueprint": blueprint,
            }

        if "corrected_blueprint" not in result:
            result["corrected_blueprint"] = blueprint

        return result
