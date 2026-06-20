import json
from pathlib import Path


BLUEPRINT_FILE = (
    Path(__file__).parent /
    "graph_blueprints.json"
)


VALID_OBJECT_TYPES = {

    "linear_graph",

    "distance_time",

    "velocity_time",

    "current_voltage",

    "photoelectric",

    "semiconductor_characteristics",

    "capacitor_charging",

    "capacitor_discharging"
}


def validate_blueprint(bp):

    errors = []

    if "question_id" not in bp:

        errors.append(
            "Missing question_id"
        )

    if "diagram_type" not in bp:

        errors.append(
            "Missing diagram_type"
        )

    elif bp["diagram_type"] != "graph":

        errors.append(
            "diagram_type must be graph"
        )

    if "object_type" not in bp:

        errors.append(
            "Missing object_type"
        )

    elif bp["object_type"] not in VALID_OBJECT_TYPES:

        errors.append(
            f"Invalid object_type: {bp['object_type']}"
        )

    return errors


def main():

    with open(
        BLUEPRINT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        blueprints = json.load(f)

    print()
    print(
        "GRAPH VALIDATION REPORT"
    )

    print("=" * 60)

    for bp in blueprints:

        errors = validate_blueprint(bp)

        print()
        print(bp["question_id"])

        if len(errors) == 0:

            print("VALID : True")
            print(" ✓ Passed")

        else:

            print("VALID : False")

            for err in errors:

                print(
                    f" - {err}"
                )

    print()


if __name__ == "__main__":
    main()