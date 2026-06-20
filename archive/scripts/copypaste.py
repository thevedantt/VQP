import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_JSON = SCRIPT_DIR.parent / "backend" / "app" / "data" / "diagram_library" / "seed_questions.json"
OUTPUT_TXT = SCRIPT_DIR / "all_seed_questions.txt"

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

lines = []

for category, questions in data.items():
    lines.append("=" * 80)
    lines.append(category.upper())
    lines.append("=" * 80)
    lines.append("")

    for idx, q in enumerate(questions, start=1):
        lines.append(f"{idx}. {q['question']}")
        lines.append("")

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Saved: {OUTPUT_TXT}")