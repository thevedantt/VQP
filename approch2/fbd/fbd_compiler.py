import json
import sys
from pathlib import Path

from fbd_validation import validate_blueprint
from fbd_layout import generate_layout
from fbd_renderer import render_svg


BLUEPRINT_FILE = Path(__file__).parent / "fbd_blueprints.json"
OUTPUT_DIR = Path(__file__).parent / "output"


def compile_all():
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(BLUEPRINT_FILE, "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    results = []

    for bp in blueprints:
        qid = bp["question_id"]

        errors = validate_blueprint(bp)

        if errors:
            results.append((qid, False, None, errors))
            continue

        layout = generate_layout(bp)

        svg = render_svg(layout)

        output_path = OUTPUT_DIR / f"{qid}.svg"
        output_path.write_text(svg, encoding="utf-8")

        results.append((qid, True, output_path, []))

    return results


def print_report(results):
    ok_count = 0
    fail_count = 0

    print()
    print("FREE BODY COMPILER REPORT")
    print("=" * 58)

    for qid, valid, path, errors in results:
        print()
        print("=" * 58)
        print(qid)
        print(f"VALID : {valid}")

        if valid:
            print(f"SVG   : {path}")
            ok_count += 1
        else:
            for e in errors:
                print(f"  - {e}")
            fail_count += 1

    print()
    print("=" * 58)
    print(f"COMPILED : {ok_count} OK, {fail_count} FAILED")
    print()


def main():
    results = compile_all()
    print_report(results)
    return 0 if all(r[1] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
