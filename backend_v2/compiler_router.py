
from pathlib import Path


APPROCH2_ROOT = Path(
    r"C:\CODES\VQP\approch2"
)


COMPILER_MAP = {

    "ray":
    APPROCH2_ROOT /
    "ray" /
    "ray_compiler.py",

    "circuit":
    APPROCH2_ROOT /
    "circuit" /
    "circuit_compiler.py",

    "fbd":
    APPROCH2_ROOT /
    "fbd" /
    "fbd_compiler.py",

    "magnetic":
    APPROCH2_ROOT /
    "magnetic_field" /
    "mf_compiler.py",

    "semiconductor":
    APPROCH2_ROOT /
    "semiconductor" /
    "semi_compiler.py",

    "graph":
    APPROCH2_ROOT /
    "graph" /
    "graph_compiler.py"
}


class CompilerRouter:

    def get_compiler(
        self,
        family: str
    ):

        family = family.lower()

        if family not in COMPILER_MAP:

            raise ValueError(
                f"Unknown family: {family}"
            )

        compiler_path = (
            COMPILER_MAP[
                family
            ]
        )

        if not compiler_path.exists():

            raise FileNotFoundError(
                f"Compiler not found: "
                f"{compiler_path}"
            )

        return {

            "family":
            family,

            "compiler_path":
            str(
                compiler_path
            )
        }


def main():

    family = input(
        "Family: "
    )

    router = (
        CompilerRouter()
    )

    result = (
        router.get_compiler(
            family
        )
    )

    print()

    print("=" * 60)
    print(
        "COMPILER ROUTER"
    )
    print("=" * 60)

    print()

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )


if __name__ == "__main__":
    main()
