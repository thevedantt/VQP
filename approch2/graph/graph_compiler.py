import json
from pathlib import Path

from graph_validation import (
    validate_blueprint,
    BLUEPRINT_FILE
)
from graph_renderer import render_graph, OUTPUT_DIR


OUTPUT_DIR.mkdir(exist_ok=True)


def compile_all():

    with open(
        BLUEPRINT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        blueprints = json.load(f)

    results = []

    for bp in blueprints:

        qid = bp.get(
            "question_id",
            "UNKNOWN"
        )

        errors = validate_blueprint(bp)

        if len(errors) > 0:

            results.append({
                "qid": qid,
                "valid": False,
                "errors": errors,
                "path": None
            })

            continue

        path = OUTPUT_DIR / f"{qid}.svg"

        try:

            render_graph(
                bp["object_type"],
                path
            )

            results.append({
                "qid": qid,
                "valid": True,
                "errors": [],
                "path": path
            })

        except Exception as e:

            results.append({
                "qid": qid,
                "valid": False,
                "errors": [str(e)],
                "path": None
            })

    return results


def print_report(results):

    ok = sum(
        1 for r in results if r["valid"]
    )

    failed = len(results) - ok

    print()
    print(
        "GRAPH COMPILER REPORT"
    )
    print(
        "=" * 66
    )

    for r in results:

        print()
        print(
            "=" * 66
        )

        print(
            f"  {r['qid']}"
        )

        if r["valid"]:

            print(
                "  VALID : True"
            )
            print(
                f"  SVG   : {r['path'].as_posix()}"
            )

        else:

            print(
                "  VALID : False"
            )

            for e in r["errors"]:

                print(
                    f"  ERROR : {e}"
                )

    print()
    print(
        "=" * 66
    )
    print(
        f"  COMPILED: {ok} OK,"
        f" {failed} FAILED"
    )
    print(
        "=" * 66
    )
    print()


def main():

    results = compile_all()

    print_report(results)


if __name__ == "__main__":
    main()
