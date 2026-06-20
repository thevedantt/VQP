import json
from pathlib import Path


FAMILIES = [

    "ray",

    "circuit",

    "fbd",

    "magnetic",

    "semiconductor",

    "graph"
]


SYSTEM_PROMPT = """
You are a Physics Diagram Classifier.

Determine:

1. Does the question require a diagram?

2. If yes, which family?

Families:

ray
circuit
fbd
magnetic
semiconductor
graph

Return ONLY JSON.

Example:

{
  "diagram_required": true,
  "family": "ray"
}
"""


def build_prompt(question):

    return f"""
Question:

{question}

{SYSTEM_PROMPT}
"""


def main():

    question = input(
        "Question: "
    )

    prompt = build_prompt(
        question
    )

    print()
    print("=" * 60)
    print("PROMPT")
    print("=" * 60)
    print(prompt)


if __name__ == "__main__":
    main()