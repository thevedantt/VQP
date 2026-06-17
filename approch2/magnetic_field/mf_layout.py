import json
from pathlib import Path


BLUEPRINT_FILE = (
    Path(__file__).parent /
    "mf_blueprints.json"
)


def generate_layout(bp):

    object_type = bp["object_type"]

    layout = {
        "question_id": bp["question_id"],
        "object_type": object_type
    }

    if object_type == "straight_conductor":

        layout["center"] = {
            "x": 400,
            "y": 300
        }

    elif object_type == "circular_loop":

        layout["center"] = {
            "x": 400,
            "y": 300
        }

        layout["radius"] = 100

    elif object_type == "solenoid":

        layout["start"] = {
            "x": 200,
            "y": 300
        }

        layout["end"] = {
            "x": 600,
            "y": 300
        }

    elif object_type == "bar_magnet":

        layout["start"] = {
            "x": 250,
            "y": 300
        }

        layout["end"] = {
            "x": 550,
            "y": 300
        }

    elif object_type == "earth_magnetism":

        layout["center"] = {
            "x": 400,
            "y": 300
        }

        layout["radius"] = 120

    elif object_type == "current_loop":

        layout["center"] = {
            "x": 400,
            "y": 300
        }

        layout["radius"] = 100

    elif object_type == "uniform_field":

        layout["area"] = {
            "x": 200,
            "y": 150,
            "width": 400,
            "height": 300
        }

    elif object_type == "charged_particle":

        layout["center"] = {
            "x": 400,
            "y": 300
        }

    elif object_type == "velocity_selector":

        layout["area"] = {
            "x": 200,
            "y": 150,
            "width": 400,
            "height": 300
        }

    elif object_type == "cyclotron":

        layout["center"] = {
            "x": 400,
            "y": 300
        }

        layout["radius"] = 180

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
        "MAGNETIC FIELD LAYOUT REPORT"
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