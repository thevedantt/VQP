import json
from pathlib import Path


BLUEPRINT_FILE = Path(__file__).parent / "fbd_blueprints.json"


VALID_OBJECT_TYPES = {
    "block",
    "inclined_plane",
    "hanging_mass",
    "magnetic_dipole",
    "lift",
    "inclined_plane_friction",
    "two_body_pulley"
}


VALID_DIRECTIONS = {
    "up",
    "down",
    "left",
    "right",
    "perpendicular",
    "vertical_down",
    "up_right"
}


VALID_STYLES = {"solid", "dashed"}


def validate_blueprint(bp):

    errors = []

    if "question_id" not in bp:
        errors.append("Missing question_id")

    if "diagram_type" not in bp:
        errors.append("Missing diagram_type")

    if bp.get("diagram_type") != "free_body":
        errors.append("diagram_type must be free_body")

    object_type = bp.get("object_type")

    if object_type not in VALID_OBJECT_TYPES:
        errors.append(
            f"Invalid object_type: {object_type}"
        )

    forces = bp.get("forces")

    if not isinstance(forces, list):
        errors.append("forces must be a list")
        return errors

    if len(forces) == 0:
        errors.append("forces list is empty")

    for i, force in enumerate(forces):

        if "label" not in force:
            errors.append(
                f"Force {i}: missing label"
            )

        if "direction" not in force:
            errors.append(
                f"Force {i}: missing direction"
            )
            continue

        direction = force["direction"]

        if direction not in VALID_DIRECTIONS:
            errors.append(
                f"Force {i}: invalid direction '{direction}'"
            )

        magnitude = force.get("magnitude", 1.0)
        if not isinstance(magnitude, (int, float)) or magnitude <= 0:
            errors.append(
                f"Force {i}: magnitude must be a positive number"
            )

        style = force.get("style", "solid")
        if style not in VALID_STYLES:
            errors.append(
                f"Force {i}: invalid style '{style}'"
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
    print("FREE BODY VALIDATION REPORT")
    print("=" * 60)

    for bp in blueprints:

        errors = validate_blueprint(bp)

        print()
        print(bp["question_id"])

        if len(errors) == 0:
            print("VALID : True")
            print(" OK")
        else:
            print("VALID : False")

            for e in errors:
                print(f" - {e}")

    print()


if __name__ == "__main__":
    main()
