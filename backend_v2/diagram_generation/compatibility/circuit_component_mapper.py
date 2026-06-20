"""
Circuit component compatibility layer (Phase 4.8, Issue 1).

approch2/circuit only understands a fixed set of passive/measuring
component types (see SUPPORTED_CIRCUIT_COMPONENTS below, mirrored from
approch2/circuit/circuit_rules.py::COMPONENT_TYPES). Backend blueprints
and LLM output sometimes use synonyms ("lamp" for "bulb", "rheostat" for
"variable_resistor") or genuinely semiconductor devices ("diode", "led")
that have no circuit-compiler equivalent at all.

This module:
  1. Documents the compatibility table (supported vs. aliasable vs.
     semiconductor-only component names).
  2. Aliases synonyms to their supported circuit equivalent.
  3. Flags semiconductor-only devices so the caller can fail loudly with
     a clear, actionable error instead of the compiler's opaque
     "unsupported type" message - or reroute the question to the
     semiconductor family before it ever reaches the circuit compiler.
"""

import copy

# Mirrors approch2/circuit/circuit_rules.py::COMPONENT_TYPES - the
# complete compatibility table of names the circuit compiler accepts.
SUPPORTED_CIRCUIT_COMPONENTS = frozenset({
    "cell",
    "battery",
    "switch",
    "key",
    "resistor",
    "variable_resistor",
    "unknown_resistor",
    "bulb",
    "ammeter",
    "voltmeter",
    "galvanometer",
    "potentiometer",
    "wire",
    "capacitor",
    "inductor",
    "ac_source",
})

# Backend/LLM synonyms that map directly onto a supported circuit type.
COMPONENT_ALIASES = {
    "battery_cell": "battery",
    "dc_source": "battery",
    "voltage_source": "battery",
    "emf_source": "battery",
    "cell_battery": "cell",
    "lamp": "bulb",
    "light_bulb": "bulb",
    "incandescent_bulb": "bulb",
    "rheostat": "variable_resistor",
    "variable_rheostat": "variable_resistor",
    "fixed_resistor": "resistor",
    "unknown_resistance": "unknown_resistor",
    "unknown_value_resistor": "unknown_resistor",
    "open_switch": "switch",
    "closed_switch": "switch",
    "toggle_switch": "switch",
    "plug_key": "key",
    "tap_key": "key",
    "conducting_wire": "wire",
    "connecting_wire": "wire",
    "copper_wire": "wire",
    "galvanometer_coil": "galvanometer",
    "ac_generator": "ac_source",
    "alternator": "ac_source",
    "ac_supply": "ac_source",
}

# Genuinely semiconductor devices - no circuit-compiler equivalent exists
# (or ever should; they're nonlinear devices, not passive components).
# A blueprint containing any of these belongs to family="semiconductor".
SEMICONDUCTOR_ONLY_COMPONENTS = frozenset({
    "diode",
    "junction_diode",
    "rectifier_diode",
    "pn_junction",
    "p_n_junction",
    "zener_diode",
    "zener",
    "led",
    "photodiode",
    "solar_cell",
    "transistor",
    "npn_transistor",
    "pnp_transistor",
})


def _normalize(raw_type):
    return (raw_type or "").strip().lower().replace(" ", "_").replace("-", "_")


def resolve_component_type(raw_type):
    """
    Resolve a raw component type name against the compatibility table.

    Returns:
        {
            "resolved_type": str,
            "action": "supported" | "aliased" | "reroute_semiconductor" | "unsupported",
            "original_type": str,
        }
    """
    normalized = _normalize(raw_type)

    if normalized in SUPPORTED_CIRCUIT_COMPONENTS:
        return {"resolved_type": normalized, "action": "supported", "original_type": raw_type}

    if normalized in COMPONENT_ALIASES:
        return {
            "resolved_type": COMPONENT_ALIASES[normalized],
            "action": "aliased",
            "original_type": raw_type,
        }

    if normalized in SEMICONDUCTOR_ONLY_COMPONENTS:
        return {
            "resolved_type": normalized,
            "action": "reroute_semiconductor",
            "original_type": raw_type,
        }

    return {"resolved_type": normalized, "action": "unsupported", "original_type": raw_type}


def check_blueprint_compatibility(blueprint):
    """
    Scan an (adapted) circuit blueprint's components for compatibility
    issues without mutating it.

    Returns:
        {
            "compatible": bool,           # no unsupported/reroute components
            "needs_reroute": bool,        # contains semiconductor-only devices
            "unsupported": [str, ...],    # raw type names that can't be aliased
            "aliased": [(original, resolved), ...],
        }
    """
    unsupported = []
    aliased = []
    needs_reroute = False

    for comp in blueprint.get("components") or []:
        if not isinstance(comp, dict):
            continue
        resolution = resolve_component_type(comp.get("type", ""))
        if resolution["action"] == "aliased":
            aliased.append((resolution["original_type"], resolution["resolved_type"]))
        elif resolution["action"] == "reroute_semiconductor":
            needs_reroute = True
            unsupported.append(resolution["original_type"])
        elif resolution["action"] == "unsupported":
            unsupported.append(resolution["original_type"])

    return {
        "compatible": not unsupported,
        "needs_reroute": needs_reroute,
        "unsupported": unsupported,
        "aliased": aliased,
    }


def apply_compatibility_fixes(blueprint):
    """
    Return a copy of the blueprint with aliasable component type names
    rewritten to their supported circuit equivalent. Components that need
    semiconductor routing or are genuinely unsupported are left untouched -
    callers must check `check_blueprint_compatibility` first.
    """
    fixed = copy.deepcopy(blueprint)
    for comp in fixed.get("components") or []:
        if not isinstance(comp, dict):
            continue
        resolution = resolve_component_type(comp.get("type", ""))
        if resolution["action"] == "aliased":
            comp["type"] = resolution["resolved_type"]
    return fixed


class CircuitRerouteError(ValueError):
    """
    Raised when a circuit blueprint contains components that have no
    circuit-compiler equivalent and must be compiled via the semiconductor
    family instead (e.g. diode, LED, transistor). Carries the offending
    component names so the caller can log/report a clear, actionable
    message instead of the compiler's raw "unsupported type" error.
    """

    def __init__(self, unsupported_components):
        self.unsupported_components = list(unsupported_components)
        names = ", ".join(sorted(set(self.unsupported_components)))
        super().__init__(
            f"Component(s) [{names}] require the semiconductor compiler, not "
            "circuit - this question was misclassified as family='circuit'. "
            "It should be routed to family='semiconductor'."
        )
