import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(
    Path(__file__).resolve().parent.parent.parent
    / ".env"
)


SYSTEM_PROMPT = """
You are a Physics Diagram Classifier.

Your task:

1. Determine if a diagram is required.
2. Determine the diagram family.

Families:

ray
circuit
fbd
magnetic
semiconductor
graph

Family disambiguation rules (read carefully):

- "circuit" is for plain passive networks: cells/batteries, resistors,
  ammeters, voltmeters, switches, wires - Kirchhoff's laws, series/parallel
  combinations, Wheatstone/meter bridge, potentiometer.
- "semiconductor" is for ANY question mentioning: PN junction, diode,
  forward bias, reverse bias, forward/reverse biasing, zener (diode),
  transistor, LED, photodiode, solar cell. These devices are nonlinear
  semiconductor devices, not basic circuit components - even if the
  question also mentions a battery or resistor in the same circuit, the
  presence of any of these keywords means family="semiconductor", NEVER
  "circuit".

Return ONLY valid JSON.

Example:

{
  "diagram_required": true,
  "family": "ray"
}
"""


class DiagramClassifier:

    def __init__(self):

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

        self.model = os.getenv(
            "OPENROUTER_MODEL",
            "openai/gpt-oss-120b:free"
        )

    def classify(self, question):

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT.strip()
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        text = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        return json.loads(text)


def main():

    classifier = DiagramClassifier()

    question = input(
        "Question: "
    )

    result = classifier.classify(
        question
    )

    print()
    print(
        json.dumps(
            result,
            indent=2
        )
    )


if __name__ == "__main__":
    main()
