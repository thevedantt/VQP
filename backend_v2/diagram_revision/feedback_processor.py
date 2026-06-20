"""
Interpret user feedback into structured change descriptions (Phase 4.5).

Uses Gemini (GEMINI_API_KEY2) to parse natural-language feedback and
produce a list of specific requested changes.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from llm.gemini_retry import call_with_retry

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROCESSOR_MODEL = "gemini-3.5-flash"

SYSTEM_PROMPT = """
You are a Feedback Interpreter for a Physics Diagram Revision System.

Given a question, current diagram family, and free-form teacher feedback,
identify the specific changes being requested.

Output ONLY valid JSON in this format:

{
  "requested_changes": [
    "Add labels to forces",
    "Show current direction with arrows"
  ]
}

Rules:
- Be specific and actionable.
- Each item must describe a single, concrete change.
- Do NOT include markdown, notes, or explanations.
- If feedback is empty or unclear, return an empty list.
"""


class FeedbackProcessor:

    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY2"))

    def process(self, question, family, feedback):
        if not feedback or not feedback.strip():
            return {"requested_changes": []}

        prompt = f"""QUESTION: {question}

FAMILY: {family}

FEEDBACK: {feedback}

Identify the specific diagram changes being requested."""

        response = call_with_retry(
            self.client.models.generate_content,
            model=PROCESSOR_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT.strip(),
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        content = response.text
        if not content:
            return {"requested_changes": []}

        text = content.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return {"requested_changes": [feedback]}

        if not isinstance(result.get("requested_changes"), list):
            result["requested_changes"] = [feedback]

        return result
