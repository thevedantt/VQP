from typing import Dict


DEFAULT_BULB_RESISTANCE = 10
DEFAULT_UNKNOWN_RESISTANCE = 5


class CircuitSolver:

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------

    def solve(self, blueprint: Dict) -> Dict:

        circuit_type = blueprint["circuit_type"]

        if circuit_type in {
            "simple_series",
            "series_resistors",
            "three_resistor_series",
            "ammeter_series",
            "cell_key_bulb"
        }:
            return self._solve_series(blueprint)

        elif circuit_type in {
            "parallel_resistors",
            "three_parallel",
            "voltmeter_parallel"
        }:
            return self._solve_parallel(blueprint)

        elif circuit_type == "wheatstone_bridge":

            return {
                "circuit_mode": "bridge",
                "message": "Wheatstone bridge solver not implemented yet"
            }

        elif circuit_type == "meter_bridge":

            return {
                "circuit_mode": "bridge",
                "message": "Meter bridge solver not implemented yet"
            }

        return {
            "equivalent_resistance": None,
            "current": None,
            "message": f"No solver implemented for {circuit_type}"
        }

    # --------------------------------------------------
    # SERIES
    # --------------------------------------------------

    def _solve_series(self, blueprint: Dict):

        voltage = self._get_voltage(blueprint)

        resistors = self._get_resistors(blueprint)

        req = sum(resistors.values())

        current = voltage / req if req > 0 else 0

        voltage_drops = {}

        for rid, resistance in resistors.items():

            voltage_drops[rid] = round(
                current * resistance,
                2
            )

        return {
            "circuit_mode": "series",
            "source_voltage": voltage,
            "equivalent_resistance": round(req, 2),
            "current": round(current, 2),
            "voltage_drops": voltage_drops
        }

    # --------------------------------------------------
    # PARALLEL
    # --------------------------------------------------

    def _solve_parallel(self, blueprint: Dict):

        voltage = self._get_voltage(blueprint)

        resistors = self._get_resistors(blueprint)

        inverse_sum = 0

        for resistance in resistors.values():

            if resistance > 0:
                inverse_sum += 1 / resistance

        req = (
            1 / inverse_sum
            if inverse_sum > 0
            else 0
        )

        total_current = (
            voltage / req
            if req > 0
            else 0
        )

        branch_currents = {}

        for rid, resistance in resistors.items():

            branch_currents[rid] = round(
                voltage / resistance,
                2
            )

        return {
            "circuit_mode": "parallel",
            "source_voltage": voltage,
            "equivalent_resistance": round(req, 2),
            "total_current": round(total_current, 2),
            "branch_currents": branch_currents
        }

    # --------------------------------------------------
    # HELPERS
    # --------------------------------------------------

    def _get_voltage(self, blueprint: Dict):

        for component in blueprint["components"]:

            if component["type"] in {
                "battery",
                "cell"
            }:
                return component.get(
                    "voltage",
                    0
                )

        return 0

    def _get_resistors(self, blueprint: Dict):

        resistors = {}

        for component in blueprint["components"]:

            component_type = component["type"]

            if component_type == "resistor":

                resistors[
                    component["id"]
                ] = component["resistance"]

            elif component_type == "bulb":

                resistors[
                    component["id"]
                ] = component.get(
                    "resistance",
                    DEFAULT_BULB_RESISTANCE
                )

            elif component_type == "unknown_resistor":

                resistors[
                    component["id"]
                ] = component.get(
                    "resistance",
                    DEFAULT_UNKNOWN_RESISTANCE
                )

        return resistors


# ------------------------------------------------------
# TEST RUNNER
# ------------------------------------------------------

if __name__ == "__main__":

    import json

    with open(
        "circuit_blueprints.json",
        "r",
        encoding="utf-8"
    ) as f:

        blueprints = json.load(f)

    solver = CircuitSolver()

    print("\nCIRCUIT SOLVER REPORT\n")

    for bp in blueprints:

        result = solver.solve(bp)

        print("=" * 60)
        print(bp["question_id"])
        print(result)

