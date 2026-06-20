"""
Graph adapter (Phase 4.2).

Transforms the backend graph blueprint into the APPROCH2 format,
normalizing LLM-generated object_type values to the exact set
expected by graph_renderer.py.
"""

import re

# Map LLM-generated descriptions to valid APPROCH2 object_type values.
OBJECT_TYPE_MAP = {
    "linear": "linear_graph",
    "linear graph": "linear_graph",
    "distance time": "distance_time",
    "distance-time": "distance_time",
    "distance_time": "distance_time",
    "velocity time": "velocity_time",
    "velocity-time": "velocity_time",
    "velocity_time": "velocity_time",
    "current voltage": "current_voltage",
    "current-voltage": "current_voltage",
    "current_voltage": "current_voltage",
    "i-v": "current_voltage",
    "iv": "current_voltage",
    "photoelectric": "photoelectric",
    "photoelectric current": "photoelectric",
    "photoelectric effect": "photoelectric",
    "semiconductor characteristics": "semiconductor_characteristics",
    "semiconductor": "semiconductor_characteristics",
    "v-i characteristic": "semiconductor_characteristics",
    "vi characteristic": "semiconductor_characteristics",
    "capacitor charging": "capacitor_charging",
    "charging": "capacitor_charging",
    "capacitor discharging": "capacitor_discharging",
    "discharging": "capacitor_discharging",
    "solar cell": "current_voltage",
    "solar cell characteristic": "current_voltage",
}

VALID_TYPES = {
    "linear_graph", "distance_time", "velocity_time", "current_voltage",
    "photoelectric", "semiconductor_characteristics",
    "capacitor_charging", "capacitor_discharging",
}

_WORD_RE = re.compile(r"[a-z0-9_]+")


def _normalize_object_type(raw: str) -> str:
    if not raw:
        return "linear_graph"
    raw_lower = raw.lower().strip()
    # Direct lookup
    if raw_lower in OBJECT_TYPE_MAP:
        return OBJECT_TYPE_MAP[raw_lower]
    # Try fuzzy match via word tokens
    words = sorted(_WORD_RE.findall(raw_lower))
    key = " ".join(words)
    if key in OBJECT_TYPE_MAP:
        return OBJECT_TYPE_MAP[key]
    # Check if any valid type is contained in the raw
    for vt in sorted(VALID_TYPES, key=len, reverse=True):
        if vt in raw_lower:
            return vt
    return "linear_graph"


def adapt(blueprint: dict) -> dict:
    if not isinstance(blueprint, dict):
        return blueprint

    return {
        "question_id": blueprint.get("question_id", ""),
        "diagram_type": blueprint.get("diagram_type", "graph"),
        "object_type": _normalize_object_type(
            blueprint.get("object_type", "")
        ),
        "x_axis": blueprint.get("x_axis", {"label": ""}),
        "y_axis": blueprint.get("y_axis", {"label": ""}),
        "curve_type": blueprint.get("curve_type", ""),
        "key_points": blueprint.get("key_points", []),
    }
