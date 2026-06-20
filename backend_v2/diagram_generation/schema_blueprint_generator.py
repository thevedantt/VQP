"""
Schema Blueprint Generator (Phase 4.1, Task 2).

Generates a blueprint from scratch using only the schema when no suitable
example exists (similarity < SIMILARITY_THRESHOLD). This is the SCHEMA_BASED
generation mode — the fallback when EXAMPLE_BASED retrieval + modification
would produce poor results.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")

SYSTEM_PROMPT = """
You are a Physics Diagram Blueprint Generator.

Generate a blueprint strictly following the provided schema.

RULES:

1. Follow the schema structure exactly.
2. Do not invent fields that are not defined by the schema.
3. Do not modify the schema structure.
4. Use only fields defined by the schema.
5. Return ONLY valid JSON, no markdown, no explanation.

Format:

{
  "blueprint": { ... }
}
"""


class SchemaBlueprintGenerator:

    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    def build_prompt(self, question, family, schema):
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
QUESTION
====================================================

{question}

====================================================

Generate a blueprint for this question strictly following the schema above.
Return ONLY:

{{
  "blueprint": {{ ... }}
}}
"""

    def generate_blueprint(self, question, family, schema):
        prompt = self.build_prompt(question, family, schema)

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
            return {"blueprint": None}

        text = content.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return {"blueprint": None}

        if "blueprint" not in result:
            result = {"blueprint": result}

        return result


def main():
    family = input("Family: ")
    question = input("Question: ")

    schema_path = (
        Path(__file__).resolve().parent.parent
        / "schemas" / family / f"{family}_schema.json"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    generator = SchemaBlueprintGenerator()
    result = generator.generate_blueprint(question, family, schema)

    print()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
