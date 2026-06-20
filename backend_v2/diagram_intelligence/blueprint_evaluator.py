import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(
    Path(__file__).resolve().parent.parent.parent
    / ".env"
)


EVALUATOR_MODEL = os.getenv(
    "OPENROUTER_MODEL2",
    "qwen/qwen3-235b-a22b-thinking-2507"
)

EVALUATOR_API_KEY = os.getenv(
    "OPENROUTER_API_KEY1"
)

EVALUATOR_SYSTEM_PROMPT = """
You are a Physics Diagram Reviewer.

Your job is NOT to regenerate the blueprint.

Compare:

1. Question
2. Schema
3. Generated Blueprint
4. Example Blueprints

Determine:

- Missing fields
- Missing labels
- Missing annotations
- Missing rendering hints
- Physics inconsistencies

Return an enhanced blueprint.

RULES:

1. Never remove required fields.
2. Never change schema structure.
3. Never invent unsupported renderer fields.
4. Only improve the blueprint.

Return ONLY JSON.

Format:

{
  "valid": true,
  "issues_found": [],
  "improvements": [],
  "enhanced_blueprint": { ... }
}

If no improvements are needed, return the original blueprint as enhanced_blueprint.
"""


class BlueprintEvaluator:

    def __init__(self):

        self.client = OpenAI(

            base_url=
            "https://openrouter.ai/api/v1",

            api_key=EVALUATOR_API_KEY
        )

    def build_prompt(
        self,
        question,
        family,
        schema,
        blueprint,
        examples=None
    ):

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

Compare:

1. Question
2. Schema
3. Generated Blueprint
4. Example Blueprints

Determine:

- Missing fields
- Missing labels
- Missing annotations
- Missing rendering hints
- Physics inconsistencies

Return an enhanced blueprint.

Return ONLY valid JSON in this format:

{{
  "valid": true,
  "issues_found": [],
  "improvements": [],
  "enhanced_blueprint": {{ ... }}
}}

Do NOT include markdown or explanations.
"""

    def evaluate(
        self,
        question,
        family,
        schema,
        blueprint,
        examples=None
    ):

        prompt = self.build_prompt(
            question,
            family,
            schema,
            blueprint,
            examples
        )

        response = self.client.chat.completions.create(

            model=EVALUATOR_MODEL,

            messages=[

                {
                    "role":
                    "system",

                    "content":
                    EVALUATOR_SYSTEM_PROMPT.strip()
                },

                {
                    "role":
                    "user",

                    "content":
                    prompt
                }
            ],

            temperature=0.1,

            max_tokens=8000
        )

        content = response.choices[0].message.content

        if not content:
            return {
                "valid": False,
                "issues_found": [
                    "Evaluator returned an empty response (likely truncated "
                    "reasoning on a thinking model) - using the unmodified blueprint."
                ],
                "improvements": [],
                "enhanced_blueprint": blueprint,
            }

        text = content.strip()

        if text.startswith("```"):

            text = (
                text
                .replace(
                    "```json",
                    ""
                )
                .replace(
                    "```",
                    ""
                )
                .strip()
            )

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return {
                "valid": False,
                "issues_found": [
                    "Evaluator response was not valid JSON - using the unmodified blueprint."
                ],
                "improvements": [],
                "enhanced_blueprint": blueprint,
            }

        if "enhanced_blueprint" not in result:

            result["enhanced_blueprint"] = blueprint

        return result


def main():

    question = input("Question: ")

    family = input("Family: ")

    schema_path = (
        Path(__file__).resolve().parent.parent.parent
        / "schemas" / family / f"{family}_schema.json"
    )

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as f:

        schema = json.load(f)

    examples_path = (
        Path(__file__).resolve().parent.parent.parent
        / "schemas" / family / "examples.json"
    )

    examples = []

    if examples_path.exists():

        with open(
            examples_path,
            "r",
            encoding="utf-8"
        ) as f:

            examples = json.load(f)

    blueprint_raw = input("Blueprint JSON: ")

    blueprint = json.loads(blueprint_raw)

    evaluator = BlueprintEvaluator()

    result = evaluator.evaluate(
        question,
        family,
        schema,
        blueprint,
        examples
    )

    print()
    print("=" * 60)
    print("BLUEPRINT EVALUATION REPORT")
    print("=" * 60)
    print()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
