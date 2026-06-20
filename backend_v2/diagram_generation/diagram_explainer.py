"""
Diagram explainer (Phase 4, Module 2 — upgraded Phase 4.1, Task 3).

Produces the one-sentence "why does this question need a diagram" reason
shown to the user. Now uses an LLM to generate question-specific explanations
(max 25 words, one sentence) instead of static family-level templates.
Static templates remain as fallback if the LLM call fails.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")


FALLBACK_REASONS = {
    "ray": (
        "Diagram is required to visualize image formation and image "
        "characteristics produced by the optical element."
    ),
    "circuit": (
        "Diagram is required to represent component connections and "
        "current flow in the electrical setup."
    ),
    "fbd": (
        "Diagram is required to show all forces acting on the object "
        "for force analysis."
    ),
    "magnetic": (
        "Diagram is required to visualize magnetic field direction "
        "and field distribution."
    ),
    "semiconductor": (
        "Diagram is required to illustrate biasing arrangement and "
        "carrier movement within the device."
    ),
    "graph": (
        "Diagram is required to represent the relationship between "
        "physical quantities."
    ),
}

DEFAULT_REASON = (
    "Diagram is required to visually represent the relationships "
    "described in the question."
)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
    return _client


def _llm_explain(question, family):
    """Ask the LLM for a question-specific explanation (max 25 words, one sentence)."""
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate exactly ONE sentence explaining why a "
                        "Physics question requires a diagram. "
                        "Maximum 25 words. One sentence only. "
                        "Be specific to the question, not generic."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Family: {family}\n\n"
                        f"Question: {question}\n\n"
                        f"Explain why this question needs a diagram "
                        f"(max 25 words, one sentence):"
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=60,
        )
        reason = response.choices[0].message.content.strip()
        if reason:
            return reason
    except Exception:
        pass
    return None


def explain(question, family):
    family_key = (family or "").lower().strip()
    reason = _llm_explain(question, family_key)
    if not reason:
        reason = FALLBACK_REASONS.get(family_key, DEFAULT_REASON)
    return {"reason": reason}


def main():
    question = input("Question: ")
    family = input("Family: ")

    result = explain(question, family)

    print()
    print(result["reason"])


if __name__ == "__main__":
    main()
