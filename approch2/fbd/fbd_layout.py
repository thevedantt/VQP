import json
from pathlib import Path


BLUEPRINT_FILE = Path(__file__).parent / "fbd_blueprints.json"

CENTER_X = 400
CENTER_Y = 300


def generate_layout(bp):

    object_type = bp["object_type"]

    layout = {
        "question_id": bp["question_id"],
        "object_type": object_type,
        "object_center": {
            "x": CENTER_X,
            "y": CENTER_Y
        },
        "forces": []
    }

    for force in bp["forces"]:

        magnitude = force.get("magnitude", 1.0)
        style = force.get("style", "solid")
        direction = force["direction"]

        if direction == "up":
            x1, y1 = CENTER_X, CENTER_Y
            x2, y2 = CENTER_X, CENTER_Y - 120 * magnitude

        elif direction == "down":
            x1, y1 = CENTER_X, CENTER_Y
            x2, y2 = CENTER_X, CENTER_Y + 120 * magnitude

        elif direction == "left":
            x1, y1 = CENTER_X, CENTER_Y
            x2, y2 = CENTER_X - 120 * magnitude, CENTER_Y

        elif direction == "right":
            x1, y1 = CENTER_X, CENTER_Y
            x2, y2 = CENTER_X + 120 * magnitude, CENTER_Y

        elif direction == "perpendicular":
            x1, y1 = CENTER_X, CENTER_Y
            x2, y2 = CENTER_X - 60 * magnitude, CENTER_Y - 80 * magnitude

        elif direction == "vertical_down":
            x1, y1 = CENTER_X, CENTER_Y
            x2, y2 = CENTER_X, CENTER_Y + 130 * magnitude

        elif direction == "up_right":
            x1, y1 = CENTER_X, CENTER_Y
            x2, y2 = CENTER_X + 90 * magnitude, CENTER_Y - 45 * magnitude

        else:
            continue

        layout["forces"].append({
            "label": force["label"],
            "direction": direction,
            "magnitude": magnitude,
            "style": style,
            "start": {"x": round(x1, 1), "y": round(y1, 1)},
            "end": {"x": round(x2, 1), "y": round(y2, 1)}
        })

    return layout


def main():

    with open(
        BLUEPRINT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        blueprints = json.load(f)

    print()
    print("FREE BODY LAYOUT REPORT")
    print("=" * 60)

    for bp in blueprints:

        layout = generate_layout(bp)

        print()
        print(layout["question_id"])
        print(layout)

    print()


if __name__ == "__main__":
    main()
