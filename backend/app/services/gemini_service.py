"""Gemini-backed AI service for question generation and physics analysis.

All LLM calls go through Gemini with strict JSON mode, low temperature,
and robust error handling.

Cascade:
    Gemini -> local template/local generator (always succeeds)
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from google import genai
from google.genai import types as genai_types

from app.core.exceptions import GeminiServiceError
from app.models.enums import DifficultyLevel, DiagramType, QuestionType
from app.services.prompt_builder import (
    build_physics_analysis_prompt,
    build_question_prompt,
    normalize_question_response,
)

logger = logging.getLogger(__name__)


def _clean_json_response(text: str) -> str:
    """Remove markdown code fences and leading/trailing whitespace from a
    Gemini response that should contain raw JSON."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)
    return text.strip()


def _parse_json_safely(text: str, label: str = "response") -> dict[str, Any] | None:
    """Attempt to parse *text* as JSON, cleaning markdown fences first.

    Returns the parsed dict on success, or ``None`` on failure (and logs the
    malformed content at warning level).
    """
    cleaned = _clean_json_response(text)
    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            logger.warning("Gemini %s parsed but is not a dict (type=%s)", label, type(data).__name__)
            return None
        return data
    except json.JSONDecodeError as exc:
        logger.warning(
            "Gemini %s JSON parse failed: %s\nRaw content (first 500 chars): %.500s",
            label, exc, text,
        )
        return None


class GeminiService:
    """Wraps the Gemini API for CBSE question generation and physics analysis.

    All calls use ``response_mime_type="application/json"`` and a low
    temperature (0.1-0.2) for deterministic, structured JSON output.
    """

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
                "GEMINI_API_KEY is not configured - GeminiService is unavailable."
            )

    @property
    def is_configured(self) -> bool:
        """Whether a real Gemini API key is configured."""
        return self._enabled

    def _call(
        self,
        prompt: str,
        temperature: float,
        label: str = "unspecified",
    ) -> str:
        """Low-level Gemini generate_content call with timing and token logging.

        Raises ``GeminiServiceError`` on failure.
        """
        if not self._enabled:
            raise GeminiServiceError("Gemini is not configured (GEMINI_API_KEY missing).")

        t0 = time.perf_counter()
        logger.info("Gemini request started [%s]", label)

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=temperature,
                ),
            )
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            logger.error(
                "Gemini API call failed [%s] after %.2fs: %s",
                label, elapsed, exc,
            )
            raise GeminiServiceError(
                f"Gemini API call failed for '{label}'.",
                detail=str(exc),
            ) from exc

        elapsed = time.perf_counter() - t0
        logger.info("Gemini response received [%s] in %.2fs", label, elapsed)

        # Log token usage if available.
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            logger.info(
                "Gemini token usage [%s]: %s",
                label,
                {
                    "prompt_tokens": getattr(usage, "prompt_token_count", None),
                    "candidates_tokens": getattr(usage, "candidates_token_count", None),
                    "total_tokens": getattr(usage, "total_token_count", None),
                },
            )

        return response.text

    # ------------------------------------------------------------------
    # Question Generation
    # ------------------------------------------------------------------
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

        Raises ``GeminiServiceError`` if not configured or if generation
        fails after all retries.
        """
        if not self._enabled:
            raise GeminiServiceError("Gemini is not configured (GEMINI_API_KEY missing).")

        prompt = build_question_prompt(
            chapter, difficulty, marks, question_type, context,
            require_diagram, diagram_type_hint,
        )
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                text = self._call(prompt, temperature=0.2, label=f"generate_question/{chapter}/{question_type}/attempt_{attempt}")
                data = _parse_json_safely(text, label="generate_question")
                if data is None:
                    raise ValueError("Failed to parse Gemini response as JSON dict.")
                result = normalize_question_response(data, chapter, difficulty, marks, question_type, diagram_type_hint)
                logger.info(
                    "Gemini question generation succeeded [%s/%s] (attempt %d/%d)",
                    chapter, question_type, attempt, self._max_retries,
                )
                return result
            except (json.JSONDecodeError, ValueError, KeyError) as exc:
                last_error = exc
                logger.warning(
                    "Gemini response parsing failed [%s/%s] (attempt %d/%d): %s",
                    chapter, question_type, attempt, self._max_retries, exc,
                )
            except GeminiServiceError:
                raise
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Gemini API call failed [%s/%s] (attempt %d/%d): %s",
                    chapter, question_type, attempt, self._max_retries, exc,
                )

            if attempt < self._max_retries:
                time.sleep(self._retry_backoff * attempt)

        raise GeminiServiceError(
            f"Gemini failed to generate a {question_type} question for chapter '{chapter}' "
            f"after {self._max_retries} attempt(s).",
            detail=str(last_error),
        )

    # ------------------------------------------------------------------
    # Physics Analysis
    # ------------------------------------------------------------------
    def analyze_physics(
        self,
        question_text: str,
        vocabulary: str,
        textbook_context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Best-effort single-attempt physics understanding.

        Returns ``None`` on any failure so the caller can fall through
        to the local heuristic.
        """
        if not self._enabled:
            return None

        try:
            prompt = build_physics_analysis_prompt(question_text, vocabulary, textbook_context)
            text = self._call(prompt, temperature=0.2, label="analyze_physics")
            data = _parse_json_safely(text, label="analyze_physics")
            if data is None:
                return None
            logger.info("Gemini physics analysis succeeded")
            return data
        except GeminiServiceError as exc:
            logger.warning("Gemini physics analysis failed: %s", exc)
            return None
        except Exception as exc:
            logger.warning("Gemini physics analysis failed: %s", exc)
            return None
