"""Final-tier offline question generator.

Used only when both OpenRouter and Gemini are unavailable (no API keys
configured, or both fail after retries). Produces a normal-looking CBSE-style
question grounded in the NCERT excerpt - it must never read as a placeholder,
error message, or mention any AI provider, per the "never expose fallback
messages to users" requirement.
"""

from __future__ import annotations

import re
from typing import Any

from app.models.enums import DifficultyLevel, DiagramType, QuestionType
from app.services.prompt_builder import _DIAGRAM_PHRASES, _MCQ_TYPES
from app.services.question_service import TYPE_MARKS_MAP

_TITLE_RE = re.compile(r"^\d+(?:\.\d+)*\s*")


def _extract_topic(context: str, chapter: str) -> str:
    first_line = context.strip().splitlines()[0] if context.strip() else ""
    cleaned = _TITLE_RE.sub("", first_line).strip()
    if cleaned and len(cleaned) < 80:
        return cleaned.title()
    return chapter


def _excerpt_preview(context: str, max_chars: int = 240) -> str:
    text = " ".join(context.split())
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def generate(
    chapter: str,
    difficulty: DifficultyLevel,
    marks: int,
    question_type: QuestionType,
    context: str,
    require_diagram: bool = False,
    diagram_type_hint: DiagramType | None = None,
) -> dict[str, Any]:
    """Return a normal CBSE-style question grounded in ``context``."""

    topic = _extract_topic(context, chapter)
    preview = _excerpt_preview(context)
    marks = marks or TYPE_MARKS_MAP.get(question_type, 1)

    options: dict[str, str] = {}

    if question_type == "MCQ":
        question_text = (
            f"With reference to {topic} (chapter: {chapter}), which of the following "
            f"statements is correct?"
        )
        options = {
            "A": f"{topic} increases as the relevant physical quantity increases.",
            "B": f"{topic} decreases as the relevant physical quantity increases.",
            "C": f"{topic} remains unchanged regardless of the relevant physical quantity.",
            "D": "None of the above relations hold for this quantity.",
        }
    elif question_type == "Assertion Reason":
        question_text = (
            f"Assertion (A): {topic} is governed by the principles described for "
            f"the chapter '{chapter}'.\n"
            f"Reason (R): {preview}"
        )
        options = {
            "A": "Both A and R are true and R is the correct explanation of A.",
            "B": "Both A and R are true but R is not the correct explanation of A.",
            "C": "A is true but R is false.",
            "D": "A is false but R is true.",
        }
    elif question_type == "VSA":
        question_text = (
            f"State and briefly explain the significance of {topic} in the context of "
            f"the chapter '{chapter}'."
        )
    elif question_type == "LA":
        question_text = (
            f"Derive the relevant expression(s) associated with {topic} as discussed in "
            f"the chapter '{chapter}', and explain its physical significance with the help "
            f"of a suitable example."
        )
    elif question_type == "Case Study":
        question_text = (
            f"Read the following passage and answer the questions that follow.\n\n"
            f"{preview}\n\n"
            f"(i) Identify the key concept described in the passage.\n"
            f"(ii) Explain how this concept applies to the scenario described.\n"
            f"(iii) State one practical application of this concept."
        )
    else:  # SA and any other type
        question_text = (
            f"Explain {topic} with reference to the chapter '{chapter}'. Support your "
            f"answer with the relevant formula or relation, applying it to a suitable example."
        )

    if require_diagram and diagram_type_hint and diagram_type_hint != "none":
        question_text += " " + _DIAGRAM_PHRASES.get(diagram_type_hint, "")

    if question_type not in _MCQ_TYPES:
        options = {}

    return {
        "question": question_text,
        "options": options,
        "marks": marks,
        "chapter": chapter,
        "type": question_type,
        "difficulty": difficulty,
        "concept": topic,
        "diagram_entities": [],
        "diagram_scenario": None,
    }
