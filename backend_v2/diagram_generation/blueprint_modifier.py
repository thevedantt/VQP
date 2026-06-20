"""
Blueprint modifier (Phase 4, Module 4).

Takes the example blueprint retrieved by example_retriever.py and modifies
only the fields necessary to satisfy the new question - it never generates
a blueprint from scratch. The example library is the base; this step adapts
it.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")

SYSTEM_PROMPT = """
You are a Physics Diagram Blueprint Modifier.

You are given an EXAMPLE blueprint that was written for a different but
similar question, plus the NEW question it must now satisfy.

RULES:

1. Use the example blueprint as the base.
2. Modify ONLY the fields necessary to satisfy the new question.
3. Preserve the schema structure exactly.
4. Do not invent fields that are not in the schema or example.
5. Return ONLY valid JSON, no markdown, no explanation.

Format:

{
  "blueprint": { ... }
}
"""


class BlueprintModifier:

    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    def build_prompt(self, question, family, schema, example_blueprint):
        return f"""
====================================================
FAMILY
====================================================

{family}

====================================================
SCHEMA
====================================================

{json.dumps(schema, indent=2)}

====================================================
EXAMPLE BLUEPRINT (base to modify)
====================================================

{json.dumps(example_blueprint, indent=2)}

====================================================
NEW QUESTION
====================================================

{question}

====================================================

Modify the example blueprint to satisfy the new question. Return ONLY:

{{
  "blueprint": {{ ... }}
}}
"""

    def modify_blueprint(self, question, family, schema, example_blueprint):
        prompt = self.build_prompt(question, family, schema, example_blueprint)

        response = self.client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )

        content = response.choices[0].message.content

        if not content:
            return {"blueprint": example_blueprint}

        text = content.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return {"blueprint": example_blueprint}

        if "blueprint" not in result:
            result = {"blueprint": result}

        return result


def main():
    family = input("Family: ")
    question = input("Question: ")

    schema_path = (
        Path(__file__).resolve().parent.parent / "schemas" / family / f"{family}_schema.json"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    example_raw = input("Example Blueprint JSON: ")
    example_blueprint = json.loads(example_raw)

    modifier = BlueprintModifier()
    result = modifier.modify_blueprint(question, family, schema, example_blueprint)

    print()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
