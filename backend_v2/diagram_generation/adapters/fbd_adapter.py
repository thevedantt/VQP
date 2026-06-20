"""
FBD adapter (Phase 4.2).

The backend FBD schema already matches the APPROCH2 format.
This adapter ensures defaults for per-force fields.
"""


def adapt(blueprint: dict) -> dict:
    if not isinstance(blueprint, dict):
        return blueprint

    adapted = {
        "question_id": blueprint.get("question_id", ""),
        "diagram_type": blueprint.get("diagram_type", "free_body"),
        "object_type": blueprint.get("object_type", ""),
    }

    forces = blueprint.get("forces", [])
    adapted_forces = []
    for f in forces:
        if not isinstance(f, dict):
            continue
        adapted_forces.append({
            "label": f.get("label", ""),
            "direction": f.get("direction", "up"),
            "magnitude": f.get("magnitude", 1.0),
            "style": f.get("style", "solid"),
        })
    adapted["forces"] = adapted_forces

    return adapted
