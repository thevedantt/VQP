"""
circuit_rules.py

Schema V2 rules and type definitions.
Source of truth for component/circuit classifications.
"""

# --- All supported component types (from circuitschema.json) ---
COMPONENT_TYPES = frozenset({
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
    "ac_source"
})

# --- All supported circuit types ---
CIRCUIT_TYPES = frozenset({
    "series",
    "parallel",
    "ammeter_series",
    "voltmeter_parallel",
    "wheatstone_bridge",
    "meter_bridge",
    "potentiometer",
    "ac_circuit"
})

# --- Classification sets ---
PASSIVE_COMPONENTS = frozenset({
    "resistor",
    "variable_resistor",
    "unknown_resistor",
    "bulb",
    "wire",
    "capacitor",
    "inductor"
})

ACTIVE_COMPONENTS = frozenset({
    "battery",
    "cell",
    "ac_source"
})

MEASURING_COMPONENTS = frozenset({
    "ammeter",
    "voltmeter",
    "galvanometer",
    "potentiometer"
})

SWITCH_COMPONENTS = frozenset({
    "switch",
    "key"
})

# --- Required fields per component (from circuitschema.json) ---
COMPONENT_REQUIRED_FIELDS = frozenset({"id", "type", "from", "to"})

# --- Optional fields per component ---
COMPONENT_OPTIONAL_FIELDS = frozenset({
    "voltage", "resistance", "current",
    "length_cm", "state", "label"
})

# --- Component → value field mapping ---
COMPONENT_VALUE_FIELD = {
    "battery": "voltage",
    "cell": "voltage",
    "ac_source": "voltage",
    "resistor": "resistance",
    "variable_resistor": "resistance",
    "unknown_resistor": "resistance",
    "bulb": "resistance",
    "wire": "length_cm"
}

# --- Phase mapping for layout/solver dispatch ---
SERIES_CIRCUITS = frozenset({
    "series",
    "ammeter_series"
})

PARALLEL_CIRCUITS = frozenset({
    "parallel",
    "voltmeter_parallel"
})

BRIDGE_CIRCUITS = frozenset({
    "wheatstone_bridge",
    "meter_bridge"
})

# --- Default values ---
DEFAULT_VOLTAGE = 12.0
DEFAULT_RESISTANCE = 1.0
DEFAULT_BULB_RESISTANCE = 10.0
DEFAULT_UNKNOWN_RESISTANCE = 5.0
DEFAULT_WIRE_LENGTH = 100.0
