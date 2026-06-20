
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(
    Path(__file__).resolve().parent.parent.parent
    / ".env"
)

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent.parent
    )
)

from diagram_intelligence.router.schema_router import (
    SchemaRouter
)


OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-oss-120b:free"
)

OUTPUT_DIR = Path(
    r"C:\CODES\VQP\backend_v2"
    r"\diagram_intelligence"
    r"\blueprint_generator"
    r"\generated_blueprints"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


class BlueprintGenerator:

    def __init__(self):

        self.router = SchemaRouter()

        self.client = OpenAI(

            base_url=
            "https://openrouter.ai/api/v1",

            api_key=os.getenv(
                "OPENROUTER_API_KEY"
            )
        )

    def build_prompt(
        self,
        question,
        family,
        schema,
        examples
    ):

        return f"""
You are a Physics Diagram Blueprint Generator.

Your job is to generate a blueprint JSON.

IMPORTANT RULES:

1. Follow schema exactly.

2. Learn from examples.

3. Return ONLY valid JSON.

4. No markdown.

5. No explanation.

6. The generated blueprint MUST conform to the ray compiler schema.
   Always include ALL required fields: question_id, renderer_type,
   scenario, principal_axis, lens, focal_points, object, rays.

7. For ray diagrams, the 'scenario' field must be one of:
   "beyond_2f", "at_2f", "between_f_and_2f", "inside_f".
   Set it based on the object position described in the question.

8. Every ray in the 'rays' array must be an object with a 'type'
   field. Allowed ray types: "parallel_ray", "optical_center_ray",
   "focal_ray".

9. The 'lens' must include 'type' (set to "convex"), 'x', and
   'height' (height must be > 0).

10. The 'focal_points' must contain F1, 2F1, F2, 2F2 with
    ordering: 2F1 < F1 < F2 < 2F2.

11. The 'object' must include 'x' and 'height' (height > 0).

================================================

FAMILY

{family}

================================================

SCHEMA

{json.dumps(
    schema,
    indent=2
)}

================================================

EXAMPLES

{json.dumps(
    examples,
    indent=2
)}

================================================

QUESTION

{question}

================================================

Generate blueprint JSON now.
"""

    def generate_blueprint(
        self,
        question,
        family
    ):

        assets = (
            self.router
            .get_family_assets(
                family
            )
        )

        prompt = self.build_prompt(

            question,

            family,

            assets["schema"],

            assets["examples"]
        )

        response = (
            self.client.chat.completions.create(

                model=
                OPENROUTER_MODEL,

                messages=[

                    {
                        "role":
                        "user",

                        "content":
                        prompt
                    }
                ],

                temperature=0.1
            )
        )

        text = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

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

        blueprint = json.loads(
            text
        )

        return {

            "question":
            question,

            "family":
            family,

            "blueprint":
            blueprint
        }

    def save_blueprint(
        self,
        result
    ):

        family = (
            result["family"]
        )

        output_file = (

            OUTPUT_DIR /

            f"{family}_blueprint.json"
        )

        with open(

            output_file,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                result,

                f,

                indent=2
            )

        return output_file


def main():

    family = input(
        "Family: "
    )

    question = input(
        "Question: "
    )

    generator = (
        BlueprintGenerator()
    )

    result = (
        generator
        .generate_blueprint(

            question,

            family
        )
    )

    output_file = (
        generator
        .save_blueprint(
            result
        )
    )

    print()

    print("=" * 60)
    print(
        "BLUEPRINT GENERATED"
    )
    print("=" * 60)

    print()

    print(
        json.dumps(
            result,
            indent=2
        )
    )

    print()

    print(
        f"Saved : {output_file}"
    )


if __name__ == "__main__":
    main()
