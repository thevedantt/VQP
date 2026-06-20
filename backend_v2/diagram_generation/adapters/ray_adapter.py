"""
Ray adapter (Phase 4.2).

The backend ray schema already matches the APPROCH2 format almost exactly.
This adapter ensures all required fields exist with sensible defaults.
"""

DEFAULT_RAY = {
    "renderer_type": "ray",
    "diagram_family": "Convex Lens",
    "scenario": "between_f_and_2f",
    "principal_axis": {"y": 300},
    "lens": {"type": "convex", "x": 400, "height": 250},
    "focal_points": {"F1": 300, "2F1": 200, "F2": 500, "2F2": 600},
    "object": {"x": 250, "height": 80},
    "rays": [{"type": "parallel_ray"}],
}


def adapt(blueprint: dict) -> dict:
    if not isinstance(blueprint, dict):
        return blueprint

    adapted = {
        "question_id": blueprint.get("question_id", ""),
        "renderer_type": "ray",
    }

    for key, default in DEFAULT_RAY.items():
        if key == "question_id":
            continue
        adapted[key] = blueprint.get(key, default)

    return adapted
