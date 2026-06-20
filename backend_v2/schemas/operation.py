
# operation.py

import json
from pathlib import Path


ROOT = Path(r"C:\CODES\VQP\approch2")

OUTPUT_ROOT = Path(
    r"C:\CODES\VQP\backend_v2\schemas"
)


CONFIG = {

    "circuit": {

        "source": ROOT / "circuit" / "circuit_blueprints.json",

        "ids": [
            "C1",
            "C4",
            "C9",
            "C11"
        ]
    },

    "fbd": {

        "source": ROOT / "fbd" / "fbd_blueprints.json",

        "ids": [
            "F1",
            "F4",
            "F5",
            "F11"
        ]
    },

    "magnetic": {

        "source": ROOT / "magnetic_field" / "mf_blueprints.json",

        "ids": [
            "M1",
            "M3",
            "M4",
            "M10"
        ]
    },

    "semiconductor": {

        "source": ROOT / "semiconductor" / "semi_blueprints.json",

        "ids": [
            "S1",
            "S2",
            "S5",
            "S10"
        ]
    },

    "graph": {

        "source": ROOT / "graph" / "graph_blueprints.json",

        "ids": [
            "G1",
            "G4",
            "G6",
            "G8"
        ]
    }
}


def build_examples():

    print()
    print("=" * 70)
    print("BUILDING EXAMPLE FILES")
    print("=" * 70)

    for family, cfg in CONFIG.items():

        source_file = cfg["source"]

        ids = set(cfg["ids"])

        with open(
            source_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        examples = []

        for item in data:

            qid = item.get("question_id")

            if qid in ids:

                examples.append(item)

        target_dir = OUTPUT_ROOT / family

        target_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            target_dir /
            "examples.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                examples,
                f,
                indent=2
            )

        print()
        print(family.upper())
        print(f"Examples : {len(examples)}")
        print(output_file)

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":

    build_examples()
