COMPONENT_TYPES = {
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
}

CIRCUIT_TYPES = {
    "series",
    "parallel",
    "ammeter_series",
    "voltmeter_parallel",
    "wheatstone_bridge",
    "meter_bridge",
    "potentiometer",
    "ac_circuit"
}

PASSIVE_COMPONENTS = {
    "resistor",
    "variable_resistor",
    "unknown_resistor",
    "bulb",
    "wire",
    "capacitor",
    "inductor"
}

ACTIVE_COMPONENTS = {
    "battery",
    "cell",
    "ac_source"
}

MEASURING_COMPONENTS = {
    "ammeter",
    "voltmeter",
    "galvanometer",
    "potentiometer"
}

BINARY_COMPONENTS = {
    "switch",
    "key"
}

DEFAULT_VOLTAGE = 12.0
DEFAULT_RESISTANCE = 1.0
DEFAULT_BULB_RESISTANCE = 10.0
DEFAULT_UNKNOWN_RESISTANCE = 5.0
DEFAULT_WIRE_LENGTH = 100.0

SERIES_CIRCUITS = {
    "series",
    "ammeter_series"
}

PARALLEL_CIRCUITS = {
    "parallel",
    "voltmeter_parallel"
}
