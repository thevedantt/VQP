from typing import Dict

from circuit_rules import (
    DEFAULT_BULB_RESISTANCE,
    DEFAULT_UNKNOWN_RESISTANCE,
    SERIES_CIRCUITS,
    PARALLEL_CIRCUITS
)


class CircuitSolver:

    def solve(self, blueprint: Dict, topology: Dict) -> Dict:
        circuit_type = blueprint["circuit_type"]
        components = topology["components"]

        if circuit_type in SERIES_CIRCUITS:
            return self._solve_series(blueprint, components)
        elif circuit_type in PARALLEL_CIRCUITS:
            return self._solve_parallel(blueprint, components)
        elif circuit_type == "wheatstone_bridge":
            return self._solve_bridge(blueprint, components)
        elif circuit_type == "meter_bridge":
            return self._solve_meter_bridge(blueprint, components)

        return {
            "circuit_mode": "unknown",
            "message": f"No solver for {circuit_type}"
        }

    def _get_voltage(self, blueprint: Dict) -> float:
        for comp in blueprint["components"]:
            if comp["type"] in ("battery", "cell"):
                return float(comp.get("voltage", 0))
        return 0.0

    def _get_resistances(self, components: Dict) -> Dict:
        values = {}
        for cid, cdata in components.items():
            ctype = cdata["type"]
            raw = cdata.get("resistance")
            if ctype == "resistor":
                values[cid] = float(raw) if raw is not None else 0
            elif ctype == "bulb":
                values[cid] = float(raw) if raw is not None else DEFAULT_BULB_RESISTANCE
            elif ctype == "unknown_resistor":
                values[cid] = float(raw) if raw is not None else DEFAULT_UNKNOWN_RESISTANCE
        return values

    def _solve_series(self, blueprint: Dict, components: Dict) -> Dict:
        voltage = self._get_voltage(blueprint)
        resistances = self._get_resistances(components)

        req = sum(resistances.values()) if resistances else 0
        current = voltage / req if req > 0 else 0

        voltage_drops = {}
        for rid, rval in resistances.items():
            voltage_drops[rid] = round(current * rval, 2)

        return {
            "circuit_mode": "series",
            "source_voltage": voltage,
            "equivalent_resistance": round(req, 2),
            "current": round(current, 2),
            "voltage_drops": voltage_drops
        }

    def _solve_parallel(self, blueprint: Dict, components: Dict) -> Dict:
        voltage = self._get_voltage(blueprint)
        resistances = self._get_resistances(components)

        inverse_sum = 0
        for rval in resistances.values():
            if rval > 0:
                inverse_sum += 1 / rval

        req = (1 / inverse_sum) if inverse_sum > 0 else 0
        total_current = voltage / req if req > 0 else 0

        branch_currents = {}
        for rid, rval in resistances.items():
            branch_currents[rid] = round(voltage / rval, 2) if rval > 0 else 0

        return {
            "circuit_mode": "parallel",
            "source_voltage": voltage,
            "equivalent_resistance": round(req, 2),
            "total_current": round(total_current, 2),
            "branch_currents": branch_currents
        }

    def _solve_bridge(self, blueprint: Dict, components: Dict) -> Dict:
        resistances = self._get_resistances(components)
        voltage = self._get_voltage(blueprint)

        rlist = list(resistances.values())
        if len(rlist) >= 4:
            p, q, r, s = rlist[0], rlist[1], rlist[2], rlist[3]
            is_balanced = abs(p / q - r / s) < 1e-6 if q > 0 and s > 0 else False

            return {
                "circuit_mode": "bridge",
                "bridge_type": "wheatstone",
                "source_voltage": voltage,
                "is_balanced": is_balanced,
                "ratio_p_q": round(p / q, 4) if q > 0 else None,
                "ratio_r_s": round(r / s, 4) if s > 0 else None,
                "resistances": resistances,
                "message": "Wheatstone bridge analysis complete"
            }

        return {
            "circuit_mode": "bridge",
            "bridge_type": "wheatstone",
            "is_balanced": False,
            "message": "Insufficient resistors for bridge analysis"
        }

    def _solve_meter_bridge(self, blueprint: Dict, components: Dict) -> Dict:
        resistances = self._get_resistances(components)
        voltage = self._get_voltage(blueprint)

        r_known = None
        r_unknown = None

        for cid, cdata in components.items():
            if cdata["type"] == "resistor":
                r_known = float(cdata.get("resistance", 0))
            elif cdata["type"] == "unknown_resistor":
                raw = cdata.get("resistance")
                r_unknown = float(raw) if raw is not None else None

        if r_known is not None and r_unknown is not None:
            return {
                "circuit_mode": "bridge",
                "bridge_type": "meter_bridge",
                "source_voltage": voltage,
                "known_resistance": r_known,
                "unknown_resistance": r_unknown,
                "message": "Meter bridge values provided"
            }

        return {
            "circuit_mode": "bridge",
            "bridge_type": "meter_bridge",
            "source_voltage": voltage,
            "known_resistance": r_known,
            "message": "Meter bridge: unknown resistance not set (it is the unknown to be found)"
        }


if __name__ == "__main__":
    import json

    from circuit_topology import CircuitTopology

    with open("circuit_blueprints.json", "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    topologist = CircuitTopology()
    solver = CircuitSolver()

    print("\nCIRCUIT SOLVER REPORT\n")

    for bp in blueprints:
        topology = topologist.build(bp)
        result = solver.solve(bp, topology)
        print("=" * 60)
        print(f"{bp['question_id']} ({bp['circuit_type']})")
        for k, v in result.items():
            print(f"  {k}: {v}")
