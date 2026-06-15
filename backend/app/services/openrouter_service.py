"""OpenRouter-backed AI question generator (GPT-4o).

Primary tier of the AI generation cascade:

    OpenRouter GPT-4o -> Gemini (secondary) -> local template generator (final)

Generates new, CBSE-style Physics questions grounded in an NCERT excerpt via
the OpenRouter chat-completions API (OpenAI-compatible), requesting strict
JSON output. When ``OPENROUTER_API_KEY`` is not configured, or the API fails
after all retries, ``generate_question`` raises ``OpenRouterServiceError`` so
the caller can fall through to the next tier.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from app.core.exceptions import OpenRouterServiceError
from app.models.enums import DifficultyLevel, DiagramType, QuestionType
from app.services.prompt_builder import (
    build_concept_extraction_prompt,
    build_physics_analysis_prompt,
    build_question_prompt,
    normalize_question_response,
)

logger = logging.getLogger(__name__)


class OpenRouterService:
    """Wraps the OpenRouter chat-completions API for grounded CBSE question generation."""

    def __init__(
        self,
        api_key: str | None,
        model_name: str,
        base_url: str = "https://openrouter.ai/api/v1",
        max_retries: int = 2,
        retry_backoff_seconds: float = 1.0,
        request_timeout_seconds: float = 30.0,
    ) -> None:
        self._max_retries = max(1, max_retries)
        self._retry_backoff = retry_backoff_seconds
        self._enabled = bool(api_key)
        self._model_name = model_name

        if self._enabled:
            self._client = httpx.Client(
                base_url=base_url,
                timeout=request_timeout_seconds,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://visualq-pilot.local",
                    "X-Title": "VisualQ Pilot",
                },
            )
            logger.info("OpenRouterService initialized with model '%s'", model_name)
        else:
            self._client = None
            logger.warning(
                "OPENROUTER_API_KEY is not configured - OpenRouterService is unavailable as a fallback tier."
            )

    @property
    def is_configured(self) -> bool:
        """Whether a real OpenRouter API key is configured."""

        return self._enabled

    def _chat_completion(self, prompt: str, temperature: float, reasoning: bool = False) -> str:
        body: dict[str, Any] = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": temperature,
        }
        if reasoning:
            body["reasoning"] = {"enabled": True}

        response = self._client.post("/chat/completions", json=body)
        response.raise_for_status()
        payload = response.json()
        message = payload["choices"][0]["message"]
        if reasoning and message.get("reasoning"):
            logger.debug("OpenRouter reasoning trace: %s", message["reasoning"])
        return message["content"]

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

        When ``require_diagram`` is True, the prompt also asks the model to
        return concept-extraction data (entities/scenario) for the diagram in
        the same response, avoiding a separate concept-extraction call.

        Raises ``OpenRouterServiceError`` if not configured or if generation
        fails after all retries.
        """

        if not self._enabled:
            raise OpenRouterServiceError("OpenRouter is not configured (OPENROUTER_API_KEY missing).")

        prompt = build_question_prompt(chapter, difficulty, marks, question_type, context, require_diagram, diagram_type_hint)
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                content = self._chat_completion(prompt, temperature=0.7)
                data = json.loads(content)
                return normalize_question_response(data, chapter, difficulty, marks, question_type, diagram_type_hint)
            except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "OpenRouter call failed for chapter='%s' type=%s (attempt %d/%d): %s",
                    chapter, question_type, attempt, self._max_retries, exc,
                )

            if attempt < self._max_retries:
                time.sleep(self._retry_backoff * attempt)

        raise OpenRouterServiceError(
            f"OpenRouter failed to generate a {question_type} question for chapter '{chapter}' "
            f"after {self._max_retries} attempt(s).",
            detail=str(last_error),
        )

    def extract_concept(self, question_text: str) -> dict[str, Any] | None:
        """Best-effort single-attempt concept/diagram extraction. Returns ``None`` on any failure."""

        if not self._enabled:
            return None

        try:
            content = self._chat_completion(build_concept_extraction_prompt(question_text), temperature=0.2)
            data = json.loads(content)
            if not isinstance(data, dict):
                return None
            return data
        except Exception as exc:  # pragma: no cover - best-effort enrichment
            logger.warning("OpenRouter concept extraction failed: %s", exc)
            return None

    def analyze_physics(self, question_text: str, vocabulary: str) -> dict[str, Any] | None:
        """Best-effort single-attempt physics understanding. Returns ``None`` on any failure.

        Restricted to ``{diagram_required, diagram_type, chapter, concept,
        scenario, entities, confidence}`` - never coordinates or geometry.
        """

        if not self._enabled:
            return None

        try:
            content = self._chat_completion(
                build_physics_analysis_prompt(question_text, vocabulary), temperature=0.2, reasoning=True
            )
            data = json.loads(content)
            if not isinstance(data, dict):
                return None
            return data
        except Exception as exc:  # pragma: no cover - best-effort enrichment
            logger.warning("OpenRouter physics analysis failed: %s", exc)
            return None
