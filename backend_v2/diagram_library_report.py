"""
Diagram family coverage audit (Phase 4.9, Task D).

Reports, per diagram family in schemas/{family}/examples.json:
    - total example count
    - example count per concept (ray: blueprint.diagram_family, e.g.
      "Convex Lens"; circuit: circuit_type; everyone else: object_type -
      the same fields example_retriever._example_text() already reads)
    - missing concepts: canonical concepts for that family with 0 examples

A family with few examples or missing concepts is exactly why
example_retriever returns low-similarity, effectively-random matches for
questions on that concept (Phase 4.9 root cause for Tasks B/C) - this
script is read-only, it doesn't change retrieval/selection behavior.

Usage:
    python diagram_library_report.py
"""

import json
from collections import Counter
from pathlib import Path

BACKEND_V2 = Path(__file__).resolve().parent
SCHEMAS_DIR = BACKEND_V2 / "schemas"

# Field used to derive a concept label, per family - mirrors the field
# choices in diagram_generation/example_retriever.py's _example_text().
CONCEPT_FIELD = {
    "circuit": "circuit_type",
    "fbd": "object_type",
    "magnetic": "object_type",
    "semiconductor": "object_type",
    "graph": "object_type",
}

# Canonical concept list per family, used only to flag missing coverage.
# Not an exhaustive syllabus - the common exam concepts for that diagram
# family, drawn from pipeline/diagram_detector.py's FAMILY_KEYWORDS and
# standard CBSE Physics topics for that family.
CANONICAL_CONCEPTS = {
    "ray": [
        "Convex Lens", "Concave Lens", "Convex Mirror", "Concave Mirror",
        "Spherical Refracting Surface", "Plane Mirror", "Prism",
    ],
    "circuit": [
        "series", "parallel", "mixed", "wheatstone_bridge", "potentiometer", "rectifier",
    ],
    "fbd": [
        "block", "inclined_plane", "pulley", "lift", "spring", "connected_blocks",
    ],
    "magnetic": [
        "straight_conductor", "solenoid", "bar_magnet", "circular_loop", "cyclotron", "toroid",
    ],
    "semiconductor": [
        "pn_junction", "forward_bias", "reverse_bias", "zener_diode", "led",
        "photodiode", "solar_cell", "transistor", "energy_band_diagram", "nand_gate",
    ],
    "graph": [
        "linear_graph", "current_voltage", "semiconductor_characteristics",
        "capacitor_charging", "capacitor_discharging", "decay_curve",
    ],
}


def _concept_label(example, family):
    if family == "ray":
        blueprint = example.get("blueprint", example)
        return blueprint.get("diagram_family")
    field = CONCEPT_FIELD.get(family, "object_type")
    return example.get(field)


def _slug(label):
    return str(label).strip().lower().replace(" ", "_").replace("-", "_")


def audit_family(family):
    examples_path = SCHEMAS_DIR / family / "examples.json"
    if not examples_path.exists():
        return None

    with open(examples_path, "r", encoding="utf-8") as f:
        examples = json.load(f)

    concept_counts = Counter()
    for example in examples:
        label = _concept_label(example, family)
        if label:
            concept_counts[label] += 1

    canonical = CANONICAL_CONCEPTS.get(family, [])
    present_slugs = {_slug(label) for label in concept_counts}
    missing = [c for c in canonical if _slug(c) not in present_slugs]

    return {
        "family": family,
        "total_examples": len(examples),
        "concept_counts": dict(concept_counts),
        "missing_concepts": missing,
    }


def build_report():
    families = sorted(
        p.name for p in SCHEMAS_DIR.iterdir()
        if p.is_dir() and (p / "examples.json").exists()
    )
    return [audit_family(family) for family in families if audit_family(family)]


def _print_report(reports):
    print()
    print("=" * 60)
    print("DIAGRAM FAMILY COVERAGE AUDIT")
    print("=" * 60)

    for report in reports:
        print()
        print("-" * 60)
        print(report["family"].capitalize())
        print()
        print(f"Total examples: {report['total_examples']}")
        print()
        print("Concepts:")
        if report["concept_counts"]:
            for concept, count in sorted(
                report["concept_counts"].items(), key=lambda kv: -kv[1]
            ):
                print(f"  {concept} ({count})")
        else:
            print("  (none tagged)")
        print()
        print("Missing concepts (0 examples):")
        if report["missing_concepts"]:
            for concept in report["missing_concepts"]:
                print(f"  {concept} (0)")
        else:
            print("  none")

    print()
    print("=" * 60)


def main():
    _print_report(build_report())


if __name__ == "__main__":
    main()
