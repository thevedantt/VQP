import json
from pathlib import Path


BLUEPRINT_FILE = (
    Path(__file__).parent /
    "semi_blueprints.json"
)


def generate_layout(bp):

    object_type = bp["object_type"]

    layout = {
        "question_id": bp["question_id"],
        "object_type": object_type,
        "center": {
            "x": 400,
            "y": 300
        }
    }

    # PN Junction Family

    if object_type in {

        "pn_junction",

        "forward_bias",

        "reverse_bias",

        "zener_diode",

        "led",

        "photodiode"

    }:

        layout["device"] = {

            "x": 300,
            "y": 250,

            "width": 200,
            "height": 100
        }

    # Logic Gates

    elif object_type in {

        "not_gate",

        "and_gate",

        "or_gate",

        "nand_gate"

    }:

        layout["gate"] = {

            "x": 250,
            "y": 200,

            "width": 300,
            "height": 200
        }

    return layout


def main():

    with open(
        BLUEPRINT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        blueprints = json.load(f)

    print()
    print(
        "SEMICONDUCTOR LAYOUT REPORT"
    )

    print("=" * 60)

    for bp in blueprints:

        layout = generate_layout(bp)

        print()
        print(layout["question_id"])
        print(layout)

    print()


if __name__ == "__main__":
    main()