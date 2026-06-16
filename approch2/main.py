import json
import os

from renderer import SVGRenderer


def main():

    renderer = SVGRenderer()

    with open(
        "data/physics_blueprints.json",
        "r",
        encoding="utf-8"
    ) as f:

        blueprints = json.load(f)

    os.makedirs(
        "output",
        exist_ok=True
    )

    results = []

    for blueprint in blueprints:

        print(
            f"Generating "
            f"{blueprint['question_id']}..."
        )

        svg = renderer.render(
            blueprint
        )

        path = (
            f"output/"
            f"{blueprint['question_id']}.svg"
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as svg_file:

            svg_file.write(svg)

        results.append(
            {
                "question_id":
                blueprint["question_id"],

                "renderer_type":
                blueprint["renderer_type"],

                "scenario":
                blueprint["scenario"],

                "svg_path":
                path
            }
        )

        print(
            f"Saved -> {path}"
        )

    with open(
        "data/rendered_diagrams.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2
        )

    print()
    print(
        "=" * 50
    )
    print(
        f"Generated "
        f"{len(results)} diagrams"
    )
    print(
        "=" * 50
    )


if __name__ == "__main__":
    main()