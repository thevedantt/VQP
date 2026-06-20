
import json
from pathlib import Path


SCHEMA_ROOT = Path(
    r"C:\CODES\VQP\backend_v2\schemas"
)


class SchemaRouter:

    def get_family_assets(
        self,
        family: str
    ):

        family = family.lower()

        family_dir = (
            SCHEMA_ROOT /
            family
        )

        if not family_dir.exists():

            raise ValueError(
                f"Unknown family: {family}"
            )

        schema_file = (
            family_dir /
            f"{family}_schema.json"
        )

        examples_file = (
            family_dir /
            "examples.json"
        )

        if not schema_file.exists():

            raise FileNotFoundError(
                f"Schema not found: {schema_file}"
            )

        if not examples_file.exists():

            raise FileNotFoundError(
                f"Examples not found: {examples_file}"
            )

        with open(
            schema_file,
            "r",
            encoding="utf-8"
        ) as f:

            schema = json.load(f)

        with open(
            examples_file,
            "r",
            encoding="utf-8"
        ) as f:

            examples = json.load(f)

        return {

            "family": family,

            "schema": schema,

            "examples": examples,

            "schema_path": str(
                schema_file
            ),

            "examples_path": str(
                examples_file
            ),

            "num_examples": len(
                examples
            )
        }


def main():

    family = input(
        "Family: "
    )

    router = SchemaRouter()

    result = (
        router.get_family_assets(
            family
        )
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
