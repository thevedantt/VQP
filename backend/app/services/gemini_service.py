"""Gemini-backed AI question generator.

Generates new, CBSE-style Physics questions grounded in an NCERT excerpt.
Requests strict JSON output from Gemini and validates/repairs the response
shape before handing it back to the paper service. Falls back to a clearly
labeled offline "stub" question when ``GEMINI_API_KEY`` is not configured,
so the rest of the pipeline remains runnable without external credentials.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from google import genai
from google.genai import types as genai_types

from app.core.exceptions import GeminiServiceError
from app.models.enums import DifficultyLevel, DiagramType, QuestionType
from app.services.question_service import TYPE_MARKS_MAP

logger = logging.getLogger(__name__)

_MCQ_TYPES = {"MCQ", "Assertion Reason"}

# Explicit, diagram-detector-friendly instructions used to steer Gemini toward
# producing a question that naturally requires the given diagram type. Each
# phrase intentionally contains the exact wording the heuristic classifier in
# diagram_service.py looks for (e.g. "free body diagram", "circuit diagram"),
# so detection succeeds even if Gemini only partially follows instructions.
_DIAGRAM_PHRASES: dict[str, str] = {
    "free_body": "Draw the free body diagram of the object, clearly labeling all the forces acting on it.",
    "circuit": "Draw the circuit diagram for the given arrangement, clearly labeling all components.",
    "ray_diagram": "Draw the ray diagram showing the formation of the image.",
    "graph": "Draw the graph showing the variation described, with clearly labeled axes.",
    "magnetic_field": "Sketch the magnetic field lines for the given configuration, clearly indicating their direction.",
}


def _build_prompt(
    chapter: str,
    difficulty: DifficultyLevel,
    marks: int,
    question_type: QuestionType,
    context: str,
    require_diagram: bool = False,
    diagram_type_hint: DiagramType | None = None,
) -> str:
    type_instructions = {
        "MCQ": (
            "Write a single multiple-choice question with exactly four options "
            'labeled "A", "B", "C", "D" in the "options" object. Exactly one option must be correct.'
        ),
        "Assertion Reason": (
            "Write an Assertion-Reason question. The 'question' field must contain an "
            "'Assertion (A):' statement followed by a 'Reason (R):' statement. Provide the "
            "standard CBSE four-option set in 'options' (A: both A and R are true and R is the "
            "correct explanation of A; B: both A and R are true but R is not the correct "
            "explanation of A; C: A is true but R is false; D: A is false but R is true)."
        ),
        "VSA": "Write a Very Short Answer question that can be answered in 1-2 sentences or a short calculation.",
        "SA": "Write a Short Answer question that requires a brief explanation and/or a short derivation or numerical.",
        "LA": "Write a Long Answer question that requires a detailed derivation, explanation, or multi-part numerical solution.",
        "Case Study": (
            "Write a Case Study question: a short passage (2-4 sentences) describing a real-world "
            "or experimental scenario grounded in the NCERT content, followed by 2-3 sub-questions "
            "labeled (i), (ii), (iii) based on that passage."
        ),
    }.get(question_type, "Write a question appropriate for the given marks and difficulty.")

    diagram_instruction = ""
    if require_diagram and diagram_type_hint and diagram_type_hint != "none":
        phrase = _DIAGRAM_PHRASES.get(diagram_type_hint, "")
        diagram_instruction = f"""
- This question MUST require the student to draw a diagram. Include the following
  instruction verbatim as part of the "question" text: "{phrase}"
- Describe a specific, concrete scenario (the objects, forces, circuit components,
  optical setup, or quantities involved) so the diagram is meaningful and can be
  drawn directly from the question text."""

    return f"""You are an expert CBSE Class 12 Physics paper setter.

Using ONLY the NCERT textbook excerpt below as grounding material, write ONE brand-new
{difficulty}-difficulty question for the chapter "{chapter}" worth {marks} mark(s).

Requirements:
- {type_instructions}
- The question must be original CBSE-board-exam style wording. Do not copy sentences verbatim
  from the excerpt; rephrase and apply the concepts.
- The question must be solvable using only the concepts present in the excerpt.
- Keep the "question" field self-contained (include any numerical data needed to solve it).{diagram_instruction}

NCERT excerpt:
\"\"\"
{context}
\"\"\"

Respond with ONLY a JSON object matching this schema (no markdown, no commentary):
{{
  "question": "<full question text>",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "marks": {marks},
  "chapter": "{chapter}",
  "type": "{question_type}",
  "concept": "<short concept name this question tests>"
}}

If the question type does not require options, return "options" as an empty object {{}}.
"""


class GeminiService:
    """Wraps the Gemini API for grounded CBSE question generation."""

    def __init__(
        self,
        api_key: str | None,
        model_name: str,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.5,
        request_timeout_seconds: float = 30.0,
    ) -> None:
        self._max_retries = max(1, max_retries)
        self._retry_backoff = retry_backoff_seconds
        self._timeout = request_timeout_seconds
        self._enabled = bool(api_key)
        self._model_name = model_name

        if self._enabled:
            self._client = genai.Client(
                api_key=api_key,
                http_options=genai_types.HttpOptions(timeout=int(request_timeout_seconds * 1000)),
            )
            logger.info("GeminiService initialized with model '%s'", model_name)
        else:
            self._client = None
            logger.warning(
                "GEMINI_API_KEY is not configured - GeminiService will return offline "
                "placeholder questions instead of calling the Gemini API."
            )

    @property
    def is_configured(self) -> bool:
        """Whether a real Gemini API key is configured."""

        return self._enabled

    def generate_question(
        self,
        chapter: str,
        difficulty: DifficultyLevel,
        marks: int,
        question_type: QuestionType,
        context: str,
        require_diagram: bool = False,
        diagram_type_hint: DiagramType | None = None,
    ) -> dict[str, Any]:
        """Generate a single new question grounded in ``context`` NCERT excerpt.

        When ``require_diagram`` is True, the prompt is steered so the
        generated question explicitly requires a diagram of
        ``diagram_type_hint`` (e.g. "Draw the free body diagram...").
        """

        if not self._enabled:
            return self.build_placeholder_question(chapter, difficulty, marks, question_type, context, require_diagram, diagram_type_hint)

        prompt = _build_prompt(chapter, difficulty, marks, question_type, context, require_diagram, diagram_type_hint)
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.7,
                    ),
                )
                data = json.loads(response.text)
                return self._normalize_question(data, chapter, difficulty, marks, question_type)
            except (json.JSONDecodeError, KeyError, ValueError, AttributeError) as exc:
                last_error = exc
                logger.warning(
                    "Gemini response parsing failed for chapter='%s' type=%s (attempt %d/%d): %s",
                    chapter, question_type, attempt, self._max_retries, exc,
                )
            except Exception as exc:  # pragma: no cover - depends on google API runtime errors
                last_error = exc
                logger.warning(
                    "Gemini API call failed for chapter='%s' type=%s (attempt %d/%d): %s",
                    chapter, question_type, attempt, self._max_retries, exc,
                )

            if attempt < self._max_retries:
                time.sleep(self._retry_backoff * attempt)

        raise GeminiServiceError(
            f"Gemini failed to generate a {question_type} question for chapter '{chapter}' "
            f"after {self._max_retries} attempt(s).",
            detail=str(last_error),
        )

    @staticmethod
    def _normalize_question(
        data: dict[str, Any],
        chapter: str,
        difficulty: DifficultyLevel,
        marks: int,
        question_type: QuestionType,
    ) -> dict[str, Any]:
        question_text = (data.get("question") or "").strip()
        if not question_text:
            raise ValueError("Gemini response is missing a non-empty 'question' field.")

        options = data.get("options") or {}
        if not isinstance(options, dict):
            options = {}
        if question_type not in _MCQ_TYPES:
            options = {}

        return {
            "question": question_text,
            "options": {str(k): str(v) for k, v in options.items()},
            "marks": int(data.get("marks") or marks),
            "chapter": data.get("chapter") or chapter,
            "type": question_type,
            "difficulty": difficulty,
            "concept": data.get("concept"),
        }

    @staticmethod
    def build_placeholder_question(
        chapter: str,
        difficulty: DifficultyLevel,
        marks: int,
        question_type: QuestionType,
        context: str,
        require_diagram: bool = False,
        diagram_type_hint: DiagramType | None = None,
    ) -> dict[str, Any]:
        """Return a deterministic offline placeholder question.

        Used both when no Gemini API key is configured, and as a graceful
        fallback when the Gemini API fails after all retries (e.g. quota
        exhaustion) so a single failed slot does not fail the whole paper.
        """

        excerpt_preview = " ".join(context.split())[:160]
        question_text = (
            f"[AI-generated placeholder - Gemini unavailable] "
            f"Based on the NCERT topic '{chapter}' ({excerpt_preview}...), answer the following "
            f"{difficulty} {marks}-mark question."
        )

        if require_diagram and diagram_type_hint and diagram_type_hint != "none":
            question_text += " " + _DIAGRAM_PHRASES.get(diagram_type_hint, "")

        options: dict[str, str] = {}
        if question_type in _MCQ_TYPES:
            options = {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}

        return {
            "question": question_text,
            "options": options,
            "marks": marks or TYPE_MARKS_MAP.get(question_type, 1),
            "chapter": chapter,
            "type": question_type,
            "difficulty": difficulty,
            "concept": None,
        }
