
"""
circuit_rules.py
"""

COMPONENT_TYPES = {
    "battery",
    "cell",
    "resistor",
    "bulb",
    "key",
    "ammeter",
    "voltmeter",
    "galvanometer",
    "unknown_resistor"
}

CIRCUIT_TYPES = {
    "simple_series",
    "series_resistors",
    "three_resistor_series",
    "parallel_resistors",
    "three_parallel",
    "ammeter_series",
    "voltmeter_parallel",
    "cell_key_bulb",
    "wheatstone_bridge",
    "meter_bridge"
}

REQUIRED_COMPONENTS = {
    "simple_series": ["battery"],
    "series_resistors": ["battery", "resistor"],
    "three_resistor_series": ["battery", "resistor"],
    "parallel_resistors": ["battery", "resistor"],
    "three_parallel": ["battery", "resistor"],
    "ammeter_series": ["battery", "ammeter"],
    "voltmeter_parallel": ["battery", "voltmeter"],
    "cell_key_bulb": ["cell", "bulb"],
    "wheatstone_bridge": ["battery"],
    "meter_bridge": ["cell"]
}

VALID_CONNECTION_TYPES = {
    ("battery", "resistor"),
    ("battery", "key"),
    ("battery", "ammeter"),
    ("battery", "bulb"),
    ("cell", "key"),
    ("cell", "bulb"),
    ("key", "bulb"),
    ("key", "ammeter"),
    ("ammeter", "resistor"),
    ("resistor", "resistor"),
    ("resistor", "voltmeter"),
    ("resistor", "galvanometer"),
}

DEFAULT_VOLTAGE = 12
DEFAULT_RESISTANCE = 1

SERIES_CIRCUITS = {
    "simple_series",
    "series_resistors",
    "three_resistor_series",
    "ammeter_series",
    "cell_key_bulb"
}

PARALLEL_CIRCUITS = {
    "parallel_resistors",
    "three_parallel",
    "voltmeter_parallel"
}

BRIDGE_CIRCUITS = {
    "wheatstone_bridge",
    "meter_bridge"
}
