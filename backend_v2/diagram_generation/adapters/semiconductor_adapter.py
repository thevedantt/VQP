"""
Semiconductor adapter (Phase 4.2).

The backend semiconductor schema already matches the APPROCH2 format exactly.
This adapter copies fields directly with defaults.
"""


def adapt(blueprint: dict) -> dict:
    if not isinstance(blueprint, dict):
        return blueprint

    return {
        "question_id": blueprint.get("question_id", ""),
        "diagram_type": blueprint.get("diagram_type", "semiconductor"),
        "object_type": blueprint.get("object_type", ""),
        "annotations": blueprint.get("annotations", []),
        "device_properties": blueprint.get("device_properties", {
            "bias_type": "",
            "show_current": True,
        }),
    }
