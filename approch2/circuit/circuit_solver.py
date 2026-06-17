"""
circuit_solver.py

Schema V2 solver.
Responsibility: electrical calculations only.
Does NOT render, does NOT create coordinates, does NOT validate.
"""

from typing import Dict, List

from circuit_rules import (
    DEFAULT_BULB_RESISTANCE,
    DEFAULT_UNKNOWN_RESISTANCE,
    DEFAULT_VOLTAGE,
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

        elif circuit_type == "potentiometer":
            return self._solve_potentiometer(blueprint, components)

        return {
            "circuit_mode": "unknown",
            "message": f"No solver implemented for '{circuit_type}'"
        }

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _get_source_voltage(self, blueprint: Dict) -> float:
        for comp in blueprint.get("components", []):
            if comp.get("type") in ("battery", "cell"):
                return float(comp.get("voltage", DEFAULT_VOLTAGE))
        return 0.0

    def _get_resistances(self, components: Dict) -> Dict[str, float]:
        resistances: Dict[str, float] = {}
        for cid, cdata in components.items():
            ctype = cdata.get("type", "")
            raw = cdata.get("resistance")
            if ctype == "resistor":
                resistances[cid] = float(raw) if raw is not None else 0.0
            elif ctype == "bulb":
                resistances[cid] = float(raw) if raw is not None else DEFAULT_BULB_RESISTANCE
            elif ctype == "unknown_resistor":
                resistances[cid] = float(raw) if raw is not None else DEFAULT_UNKNOWN_RESISTANCE
        return resistances

    # --------------------------------------------------
    # Series solver
    # --------------------------------------------------

    def _solve_series(self, blueprint: Dict, components: Dict) -> Dict:
        voltage = self._get_source_voltage(blueprint)
        resistances = self._get_resistances(components)

        req = sum(resistances.values()) if resistances else 0.0
        current = voltage / req if req > 0 else 0.0

        voltage_drops: Dict[str, float] = {}
        for rid, rval in resistances.items():
            voltage_drops[rid] = round(current * rval, 2)

        return {
            "circuit_mode": "series",
            "source_voltage": round(voltage, 2),
            "equivalent_resistance": round(req, 2),
            "total_current": round(current, 2),
            "voltage_drops": voltage_drops,
            "components_solved": list(resistances.keys())
        }

    # --------------------------------------------------
    # Parallel solver
    # --------------------------------------------------

    def _solve_parallel(self, blueprint: Dict, components: Dict) -> Dict:
        voltage = self._get_source_voltage(blueprint)
        resistances = self._get_resistances(components)

        inv_sum = 0.0
        for rval in resistances.values():
            if rval > 0:
                inv_sum += 1.0 / rval

        req = (1.0 / inv_sum) if inv_sum > 0 else 0.0
        total_current = voltage / req if req > 0 else 0.0

        branch_currents: Dict[str, float] = {}
        for rid, rval in resistances.items():
            branch_currents[rid] = round(voltage / rval, 2) if rval > 0 else 0.0

        return {
            "circuit_mode": "parallel",
            "source_voltage": round(voltage, 2),
            "equivalent_resistance": round(req, 2),
            "total_current": round(total_current, 2),
            "branch_currents": branch_currents,
            "components_solved": list(resistances.keys())
        }

    # --------------------------------------------------
    # Wheatstone bridge solver
    # --------------------------------------------------

    def _solve_bridge(self, blueprint: Dict, components: Dict) -> Dict:
        resistances = self._get_resistances(components)
        voltage = self._get_source_voltage(blueprint)

        rlist: List[float] = list(resistances.values())

        if len(rlist) >= 4:
            p, q, r, s = rlist[0], rlist[1], rlist[2], rlist[3]
            is_balanced = False
            ratio_pq: float = 0.0
            ratio_rs: float = 0.0

            if q > 0 and s > 0:
                ratio_pq = round(p / q, 4)
                ratio_rs = round(r / s, 4)
                is_balanced = abs(ratio_pq - ratio_rs) < 1e-6

            return {
                "circuit_mode": "bridge",
                "bridge_type": "wheatstone",
                "source_voltage": round(voltage, 2),
                "is_balanced": is_balanced,
                "ratio_p_q": ratio_pq,
                "ratio_r_s": ratio_rs,
                "resistances": {k: round(v, 2) for k, v in resistances.items()},
                "message": "Wheatstone bridge is BALANCED" if is_balanced else "Wheatstone bridge is UNBALANCED"
            }

        return {
            "circuit_mode": "bridge",
            "bridge_type": "wheatstone",
            "is_balanced": False,
            "message": "Insufficient resistors for Wheatstone bridge analysis (need >= 4)"
        }

    # --------------------------------------------------
    # Meter bridge solver
    # --------------------------------------------------

    def _solve_meter_bridge(self, blueprint: Dict, components: Dict) -> Dict:
        voltage = self._get_source_voltage(blueprint)
        resistances = self._get_resistances(components)

        r_known: float = 0.0
        r_unknown: float = 0.0
        found_known = False
        found_unknown = False

        for cid, cdata in components.items():
            if cdata.get("type") == "resistor":
                raw = cdata.get("resistance")
                if raw is not None:
                    r_known = float(raw)
                    found_known = True
            elif cdata.get("type") == "unknown_resistor":
                raw = cdata.get("resistance")
                if raw is not None:
                    r_unknown = float(raw)
                    found_unknown = True

        if found_known and found_unknown:
            return {
                "circuit_mode": "bridge",
                "bridge_type": "meter_bridge",
                "source_voltage": round(voltage, 2),
                "known_resistance": r_known,
                "unknown_resistance": r_unknown,
                "message": "Meter bridge: both resistances known"
            }

        if found_known and not found_unknown:
            return {
                "circuit_mode": "bridge",
                "bridge_type": "meter_bridge",
                "source_voltage": round(voltage, 2),
                "known_resistance": r_known,
                "unknown_resistance": None,
                "message": "Meter bridge: unknown resistance TBD (it is the value to be measured)"
            }

        return {
            "circuit_mode": "bridge",
            "bridge_type": "meter_bridge",
            "message": "Meter bridge: insufficient component data"
        }


    # --------------------------------------------------
    # Potentiometer solver
    # --------------------------------------------------

    def _solve_potentiometer(self, blueprint: Dict, components: Dict) -> Dict:
        driving_cell = None
        wire_segments = {}
        r_rheostat = 0.0
        test_cell = None

        for cid, cdata in components.items():
            ctype = cdata.get("type", "")
            if ctype == "cell":
                raw = cdata.get("voltage")
                if raw is not None:
                    if driving_cell is None:
                        driving_cell = float(raw)
                    else:
                        test_cell = float(raw)
            elif ctype == "resistor":
                r_rheostat = float(cdata.get("resistance", 0))
            elif ctype == "wire":
                raw = cdata.get("length_cm")
                if raw is not None:
                    wire_segments[cid] = float(raw)

        driving_voltage = driving_cell or 0.0
        total_wire_length = sum(wire_segments.values()) if wire_segments else 0.0
        wire_resistance_ratio = total_wire_length * 0.1  # assume 0.1 ohm/cm (constantan wire)

        total_r = r_rheostat + wire_resistance_ratio
        current = driving_voltage / total_r if total_r > 0 else 0.0
        pd_ac = current * wire_resistance_ratio
        gradient = pd_ac / total_wire_length if total_wire_length > 0 else 0.0

        result = {
            "circuit_mode": "potentiometer",
            "driving_voltage": round(driving_voltage, 2),
            "rheostat_resistance": round(r_rheostat, 2),
            "total_wire_length_cm": round(total_wire_length, 2),
            "driving_current_A": round(current, 4),
            "pd_across_wire_V": round(pd_ac, 4),
            "potential_gradient_V_per_cm": round(gradient, 6),
        }

        if test_cell is not None:
            result["test_cell_voltage"] = round(test_cell, 2)
            if gradient > 0:
                null_length = test_cell / gradient
                result["null_point_length_cm"] = round(null_length, 2)
                result["message"] = (
                    f"Null point at {null_length:.2f} cm from A "
                    f"(test cell EMF = {test_cell}V)"
                )
            else:
                result["message"] = "Zero gradient — cannot determine null point"
        else:
            result["message"] = "Test cell voltage unknown (it is the value to be measured)"

        return result


if __name__ == "__main__":
    import json

    from circuit_topology import CircuitTopology

    with open("circuit_blueprints.json", "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    topologist = CircuitTopology()
    solver = CircuitSolver()

    print("=" * 64)
    print("  CIRCUIT SOLVER REPORT")
    print("=" * 64)

    for bp in blueprints:
        topology = topologist.build(bp)
        result = solver.solve(bp, topology)
        qid = bp.get("question_id", "?")
        ct = bp.get("circuit_type", "?")
        print(f"\n  {qid} ({ct})")
        for k, v in result.items():
            print(f"    {k}: {v}")

    print(f"\n{'=' * 64}")
    print("  SOLVER COMPLETE")
    print(f"{'=' * 64}")
