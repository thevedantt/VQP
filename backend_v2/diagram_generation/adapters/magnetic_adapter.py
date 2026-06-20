"""
Magnetic field adapter (Phase 4.2).

The backend magnetic schema already matches the APPROCH2 format exactly.
This adapter copies fields directly with defaults.
"""


def adapt(blueprint: dict) -> dict:
    if not isinstance(blueprint, dict):
        return blueprint

    return {
        "question_id": blueprint.get("question_id", ""),
        "diagram_type": blueprint.get("diagram_type", "magnetic_field"),
        "object_type": blueprint.get("object_type", ""),
        "labels": blueprint.get("labels", []),
        "field_properties": blueprint.get("field_properties", {
            "field_type": "",
            "show_arrows": True,
        }),
    }
