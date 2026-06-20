"""
AI question generator for CBSE Class 12 Physics papers.

Calls OpenRouter directly over HTTP (requests) - no `openai` SDK
dependency. Two model/key pairs are configured in .env:

    OPENROUTER_API_KEY  + OPENROUTER_MODEL   (primary)
    OPENROUTER_API_KEY1 + OPENROUTER_MODEL2  (fallback)

If the primary call fails (rate limit, timeout, bad response), the
fallback pair is tried before giving up. Generates one question at a
time, on demand, for whatever type/marks the question_selector needs
to fill (PYQ pool gaps, ratio top-up, or diagram-quota enforcement).
"""

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

BACKEND_V2 = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_V2 / ".env")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_CHAIN = [
    (os.getenv("OPENROUTER_API_KEY"), os.getenv("OPENROUTER_MODEL")),
    (os.getenv("OPENROUTER_API_KEY1"), os.getenv("OPENROUTER_MODEL2")),
]
MODEL_CHAIN = [(key, model) for key, model in MODEL_CHAIN if key and model]

DIAGRAM_EXAMPLES = [
    "Draw a ray diagram for an object placed between F and 2F of a convex lens.",
    "Draw a free body diagram of a block placed on an inclined plane.",
    "Draw a circuit diagram showing a cell, resistor and ammeter connected in series.",
    "Draw the magnetic field pattern around a straight current-carrying conductor.",
    "Draw the V-I characteristics of a semiconductor diode.",
]

# Marks-aware difficulty rules (Phase 3B Task 3) - keeps a 1-mark AI
# question from coming out as hard as a 5-mark one, and vice versa.
MARKS_DIFFICULTY_GUIDANCE = {
    1: "Simple recall, a simple formula application, or a simple concept check. Must be answerable in one short line - no multi-step reasoning.",
    2: "A direct numerical with one formula substitution, a definition, or short reasoning in 2-3 lines.",
    3: "One derivation step, a moderate numerical (2-3 steps), or an explanation requiring a short paragraph.",
    4: "Case-study style or multi-step reasoning across 2-3 sub-parts, but still self-contained.",
    5: "A long-answer question: a derivation, a full multi-step numerical, or a question spanning multiple concepts.",
    6: "A long-answer question: a derivation, a full multi-step numerical, or a question spanning multiple concepts.",
}

TYPE_GUIDANCE = {
    "MCQ": "A multiple-choice question with exactly 4 options labelled A, B, C, D, only one correct.",
    "Assertion Reason": (
        "An Assertion-Reason question. Inside the question text, write "
        "'Assertion (A): ...' then 'Reason (R): ...', followed by the 4 standard "
        "CBSE options: "
        "A) Both A and R are true and R is the correct explanation of A. "
        "B) Both A and R are true but R is NOT the correct explanation of A. "
        "C) A is true but R is false. "
        "D) A is false but R is true."
    ),
    "Fill in the Blanks": "A fill-in-the-blank statement with a single missing term, marked with '______'.",
    "True/False": "A single true/false statement about a physics concept.",
    "Very Short": "A very short answer question, answerable in 1-2 lines.",
    "Short Answer": "A short answer question requiring 2-3 short steps or a brief explanation.",
    "Long Answer": "A long answer question requiring a derivation, multi-step numerical, or detailed explanation.",
    "Case Study": "A case-study question: a short passage/scenario followed by 1-2 sub-questions, e.g. '(i) ...'.",
}


class AIQuestionGenerator:

    def __init__(self):
        if not MODEL_CHAIN:
            raise RuntimeError(
                "No OpenRouter API key/model pairs configured in .env "
                "(need OPENROUTER_API_KEY+OPENROUTER_MODEL or "
                "OPENROUTER_API_KEY1+OPENROUTER_MODEL2)."
            )

    def build_prompt(self, question_type, marks, require_diagram, difficulty, avoid_topics):
        guidance = TYPE_GUIDANCE.get(question_type, "A CBSE Class 12 Physics question.")

        diagram_clause = ""
        if require_diagram:
            examples = "\n".join(f"- {e}" for e in DIAGRAM_EXAMPLES)
            diagram_clause = f"""
IMPORTANT: This question MUST require a diagram to answer (ray diagram,
free body diagram, circuit diagram, magnetic field pattern, or
semiconductor characteristic graph). Phrase it explicitly, for example:
{examples}
"""

        avoid_clause = ""
        if avoid_topics:
            joined = "\n".join(f"- {t}" for t in avoid_topics[:10])
            avoid_clause = f"""
Do NOT repeat the concepts/topics already used elsewhere in this paper:
{joined}
"""

        difficulty_clause = f"Target difficulty: {difficulty}." if difficulty else ""
        marks_clause = MARKS_DIFFICULTY_GUIDANCE.get(marks)
        marks_clause = f"Marks-appropriate difficulty: {marks_clause}" if marks_clause else ""

        return f"""
You are a CBSE Class 12 Physics question paper setter.

Generate ONE question of type "{question_type}" worth {marks} mark(s).

{guidance}

{marks_clause}
{difficulty_clause}
{diagram_clause}
{avoid_clause}

Return ONLY valid JSON in this exact format:

{{
  "question": "...",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}} or null,
  "diagram_required": true or false
}}

No markdown. No explanation.
"""

    def _call_openrouter(self, api_key, model, prompt):
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()

    def generate(self, question_type, marks, require_diagram=False, difficulty=None, avoid_topics=None):
        prompt = self.build_prompt(question_type, marks, require_diagram, difficulty, avoid_topics)

        last_error = None
        for api_key, model in MODEL_CHAIN:
            try:
                text = self._call_openrouter(api_key, model, prompt)
                if text.startswith("```"):
                    text = text.replace("```json", "").replace("```", "").strip()

                data = json.loads(text)

                return {
                    "question": (data.get("question") or "").strip(),
                    "type": question_type,
                    "marks": marks,
                    "options": data.get("options"),
                    "diagram_required": bool(data.get("diagram_required", require_diagram)),
                }
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All OpenRouter model attempts failed: {last_error}")


def main():
    generator = AIQuestionGenerator()

    qtype = input("Type: ")
    marks = int(input("Marks: "))
    require_diagram = input("Require diagram? (y/n): ").strip().lower() == "y"

    result = generator.generate(qtype, marks, require_diagram=require_diagram)

    print()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
