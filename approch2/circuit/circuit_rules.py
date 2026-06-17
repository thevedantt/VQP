COMPONENT_TYPES = {
    "battery",
    "cell",
    "resistor",
    "bulb",
    "key",
    "ammeter",
    "voltmeter",
    "galvanometer",
    "unknown_resistor",
    "wire"
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

PASSIVE_COMPONENTS = {
    "resistor",
    "bulb",
    "unknown_resistor",
    "wire"
}

ACTIVE_COMPONENTS = {
    "battery",
    "cell"
}

MEASURING_COMPONENTS = {
    "ammeter",
    "voltmeter",
    "galvanometer"
}

BINARY_COMPONENTS = {
    "key"
}

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

TERMINAL_ROLES = {
    "battery": ["positive", "negative"],
    "cell": ["positive", "negative"]
}

DEFAULT_VOLTAGE = 12
DEFAULT_RESISTANCE = 1
DEFAULT_BULB_RESISTANCE = 10
DEFAULT_UNKNOWN_RESISTANCE = 5

COMPONENT_VALUE_FIELDS = {
    "battery": {"field": "voltage", "units": "V"},
    "cell": {"field": "voltage", "units": "V"},
    "resistor": {"field": "resistance", "units": "\u03a9"},
    "bulb": {"field": "resistance", "units": "\u03a9"},
    "wire": {"field": "length", "units": "cm"}
}

REQUIRED_TERMINAL_COUNT = {
    "battery": 2,
    "cell": 2,
    "resistor": 2,
    "bulb": 2,
    "key": 2,
    "ammeter": 2,
    "voltmeter": 2,
    "galvanometer": 2,
    "unknown_resistor": 2,
    "wire": 2
}

ANNOTATION_TYPES = {
    "value_label",
    "measurement",
    "current_direction",
    "voltage_polarity",
    "component_label"
}
