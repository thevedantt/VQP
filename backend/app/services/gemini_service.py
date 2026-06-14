"""Gemini-backed AI question generator.

Generates new, CBSE-style Physics questions grounded in an NCERT excerpt.
Requests strict JSON output from Gemini and validates/repairs the response
shape before handing it back to the paper service.

Acts as the **secondary** fallback in the AI generation cascade (after
OpenRouter GPT-4o, before the local template generator). When
``GEMINI_API_KEY`` is not configured, or the API fails after all retries,
``generate_question`` raises ``GeminiServiceError`` so the caller can fall
through to the next tier.
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
from app.services.prompt_builder import build_question_prompt, normalize_question_response

logger = logging.getLogger(__name__)


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
                "GEMINI_API_KEY is not configured - GeminiService is unavailable as a fallback tier."
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

        Raises ``GeminiServiceError`` if not configured or if generation
        fails after all retries.
        """

        if not self._enabled:
            raise GeminiServiceError("Gemini is not configured (GEMINI_API_KEY missing).")

        prompt = build_question_prompt(chapter, difficulty, marks, question_type, context, require_diagram, diagram_type_hint)
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
                return normalize_question_response(data, chapter, difficulty, marks, question_type, diagram_type_hint)
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

    def extract_concept(self, question_text: str) -> dict[str, Any] | None:
        """Best-effort single-attempt concept/diagram extraction. Returns ``None`` on any failure."""

        if not self._enabled:
            return None

        from app.services.prompt_builder import build_concept_extraction_prompt

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=build_concept_extraction_prompt(question_text),
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            data = json.loads(response.text)
            if not isinstance(data, dict):
                return None
            return data
        except Exception as exc:  # pragma: no cover - best-effort enrichment
            logger.warning("Gemini concept extraction failed: %s", exc)
            return None
