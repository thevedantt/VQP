"""
Circuit adapter (Phase 4.2).

Transforms the backend circuit blueprint format into the exact format
expected by the APPROCH2 CircuitCompiler.

The LLM generates separate `components` (id, type, value) and
`connections` (from, to) arrays. This adapter merges them positionally:
the Nth connection corresponds to the Nth component (or nearest match).

Backend format:
    {
        "components": [{"id": "R1", "type": "resistor", "value": 4}, ...],
        "connections": [{"from": "N1", "to": "N2"}, ...]
    }

APPROCH2 format:
    {
        "renderer_type": "circuit",
        "diagram_family": "electric_circuit",
        "circuit_type": "series",
        "nodes": ["N1", "N2", ...],
        "components": [
            {"id": "R1", "type": "resistor", "resistance": 4, "from": "N1", "to": "N2"}
        ]
    }
"""

COMPONENT_VALUE_FIELD = {
    "battery": "voltage",
    "cell": "voltage",
    "ac_source": "voltage",
    "resistor": "resistance",
    "variable_resistor": "resistance",
    "unknown_resistor": "resistance",
    "bulb": "resistance",
    "wire": "length_cm",
}

CIRCUIT_TYPE_NORMALIZE = {
    "series": "series",
    "series_circuit": "series",
    "parallel": "parallel",
    "parallel_circuit": "parallel",
    "ammeter_series": "ammeter_series",
    "voltmeter_parallel": "voltmeter_parallel",
    "wheatstone_bridge": "wheatstone_bridge",
    "meter_bridge": "meter_bridge",
    "potentiometer": "potentiometer",
    "ac_circuit": "ac_circuit",
}


def _normalize_circuit_type(raw: str) -> str:
    raw_clean = raw.lower().strip().replace(" ", "_").replace("-", "_")
    return CIRCUIT_TYPE_NORMALIZE.get(raw_clean, "series")


import re

_VALUE_CLEAN = re.compile(r"^[+-]?(\d+\.?\d*)")


def _clean_numeric(raw):
    """Strip units like '12V', '4Ω', '2 A' → float. Returns None if unparseable."""
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        m = _VALUE_CLEAN.search(raw.strip())
        if m:
            return float(m.group(1))
    return None


def _map_value(entry: dict, comp_type: str, value):
    """Map a generic `value` field to the type-specific field name, cleaning units."""
    vf = COMPONENT_VALUE_FIELD.get(comp_type)
    if vf and value is not None:
        cleaned = _clean_numeric(value)
        if cleaned is not None:
            entry[vf] = cleaned


NUMERIC_FIELDS = {"voltage", "resistance", "current", "length_cm"}


def _pass_through(entry: dict, source: dict):
    """Copy optional fields from source to entry, cleaning numerics."""
    for field in ("state", "label", "current", "voltage", "resistance", "length_cm"):
        if field in source:
            val = source[field]
            if field in NUMERIC_FIELDS:
                cleaned = _clean_numeric(val)
                if cleaned is not None:
                    entry[field] = cleaned
            else:
                entry[field] = val


def adapt(blueprint: dict) -> dict:
    if not isinstance(blueprint, dict):
        return blueprint

    adapted = {
        "question_id": blueprint.get("question_id", ""),
        "renderer_type": "circuit",
        "diagram_family": "electric_circuit",
        "circuit_type": _normalize_circuit_type(
            blueprint.get("circuit_type") or blueprint.get("circuit_mode") or "series"
        ),
    }

    backend_comps = blueprint.get("components") or []
    connections = blueprint.get("connections") or []

    # Detect already-APPROCH2 format: components have from/to
    if backend_comps and all(
        isinstance(c, dict) and c.get("from") and c.get("to") for c in backend_comps
    ):
        adapted["components"] = backend_comps
        adapted["nodes"] = sorted({
            n for c in backend_comps
            for n in (c.get("from"), c.get("to"))
            if n
        })
        return adapted

    # Build APPROCH2 components by merging connections with components.
    # Strategy: try matching by connection.id -> component.id first,
    # then fall back to positional index alignment.
    comp_by_id = {}
    for c in backend_comps:
        if isinstance(c, dict) and c.get("id"):
            comp_by_id[c["id"].lower()] = c

    approch2_comps = []
    all_nodes = set()

    for i, conn in enumerate(connections):
        if not isinstance(conn, dict):
            continue
        from_node = conn.get("from", "")
        to_node = conn.get("to", "")
        if not from_node or not to_node:
            continue

        all_nodes.add(from_node)
        all_nodes.add(to_node)

        # Try matching by id first
        conn_id = (conn.get("id") or conn.get("component_id") or "").lower()
        comp = comp_by_id.get(conn_id)

        # Fallback to positional match
        if comp is None and i < len(backend_comps):
            comp = backend_comps[i] if isinstance(backend_comps[i], dict) else None

        # Extract type from component or connection
        comp_type = ""
        if comp:
            comp_type = comp.get("type", "")
        if not comp_type and conn.get("type"):
            comp_type = conn.get("type", "")

        comp_id = (comp.get("id") if comp else None) or conn.get("id") or f"COMP_{i}"
        value = (comp.get("value") if comp else None) or conn.get("value")

        # Determine node names: prefer connection's from/to, fall back to
        # treating the node names as the component endpoints directly.
        entry = {
            "id": comp_id,
            "type": comp_type,
            "from": from_node,
            "to": to_node,
        }
        _map_value(entry, comp_type, value)
        if comp:
            _pass_through(entry, comp)
        _pass_through(entry, conn)

        approch2_comps.append(entry)

    # Filter out components with empty type (schema merge artifacts)
    approch2_comps = [c for c in approch2_comps if c.get("type")]

    # If no connections, create components using default nodes
    if not approch2_comps and backend_comps:
        for comp in backend_comps:
            if not isinstance(comp, dict) or not comp.get("id"):
                continue
            entry = {
                "id": comp["id"],
                "type": comp.get("type", ""),
                "from": "N1",
                "to": "N2",
            }
            _map_value(entry, comp.get("type", ""), comp.get("value"))
            _pass_through(entry, comp)
            all_nodes.add("N1")
            all_nodes.add("N2")
            approch2_comps.append(entry)

    adapted["components"] = approch2_comps
    adapted["nodes"] = sorted(all_nodes) if all_nodes else ["N1", "N2"]

    return adapted
