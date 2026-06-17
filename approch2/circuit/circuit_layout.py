from typing import Dict

from circuit_rules import SERIES_CIRCUITS, PARALLEL_CIRCUITS


class CircuitLayout:

    UNIT = 40

    def generate(self, topology: Dict, blueprint: Dict) -> Dict:
        circuit_type = topology["circuit_type"]
        nodes = topology["nodes"]
        components = topology["components"]

        if circuit_type in SERIES_CIRCUITS:
            return self._layout_series(topology)

        elif circuit_type in PARALLEL_CIRCUITS:
            return self._layout_parallel(topology)

        elif circuit_type == "wheatstone_bridge":
            return self._layout_bridge(topology)

        elif circuit_type == "meter_bridge":
            return self._layout_meter_bridge(topology)

        raise ValueError(f"Unsupported circuit type: {circuit_type}")

    # --------------------------------------------------
    # Series
    # --------------------------------------------------

    def _layout_series(self, topology: Dict) -> Dict:
        u = self.UNIT
        node_order = topology["node_order"]
        components = topology["components"]

        net_positions = {}
        x = 0
        for nid in node_order:
            net_positions[nid] = {"x": x, "y": 0}
            x += u

        placements = {}
        for cid, cdata in components.items():
            nfrom = cdata.get("from")
            nto = cdata.get("to")
            if nfrom in net_positions and nto in net_positions:
                p1 = net_positions[nfrom]
                p2 = net_positions[nto]
                placements[cid] = {
                    "x": (p1["x"] + p2["x"]) / 2,
                    "y": (p1["y"] + p2["y"]) / 2,
                    "type": cdata["type"],
                    "from": nfrom,
                    "to": nto
                }

        return {
            "layout_type": "series",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": self._compute_bounds(net_positions, placements)
        }

    # --------------------------------------------------
    # Parallel
    # --------------------------------------------------

    def _layout_parallel(self, topology: Dict) -> Dict:
        u = self.UNIT
        nodes = topology["nodes"]
        components = topology["components"]

        if len(nodes) < 2:
            return {
                "layout_type": "parallel",
                "net_positions": {},
                "component_placements": {},
                "bounds": {"width": 0, "height": 0}
            }

        n0 = nodes[0]
        n1 = nodes[1]
        offset = u * 2

        net_positions = {
            n0: {"x": 0, "y": -offset},
            n1: {"x": 0, "y": offset}
        }

        sources = [cid for cid, c in components.items() if c["type"] in ("battery", "cell")]
        others = [cid for cid, c in components.items() if c["type"] not in ("battery", "cell")]

        placements = {}
        col = 0

        for cid in sources:
            placements[cid] = {
                "x": 0,
                "y": 0,
                "type": components[cid]["type"]
            }

        for cid in others:
            col += 1
            placements[cid] = {
                "x": col * u * 1.5,
                "y": 0,
                "type": components[cid]["type"]
            }

        return {
            "layout_type": "parallel",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": self._compute_bounds(net_positions, placements)
        }

    # --------------------------------------------------
    # Wheatstone Bridge
    # --------------------------------------------------

    def _layout_bridge(self, topology: Dict) -> Dict:
        u = self.UNIT
        nodes = topology["nodes"]
        components = topology["components"]

        node_positions = {
            "A": {"x": 0, "y": -u * 2},
            "B": {"x": -u * 2, "y": 0},
            "C": {"x": u * 2, "y": 0},
            "D": {"x": 0, "y": u * 2}
        }

        net_positions = {}
        for nid in nodes:
            net_positions[nid] = node_positions.get(nid, {"x": 0, "y": 0})

        placements = {}
        for cid, cdata in components.items():
            nfrom = cdata.get("from")
            nto = cdata.get("to")
            if nfrom in net_positions and nto in net_positions:
                p1 = net_positions[nfrom]
                p2 = net_positions[nto]
                placements[cid] = {
                    "x": (p1["x"] + p2["x"]) / 2,
                    "y": (p1["y"] + p2["y"]) / 2,
                    "type": cdata["type"],
                    "from": nfrom,
                    "to": nto
                }

        return {
            "layout_type": "bridge",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": self._compute_bounds(net_positions, placements)
        }

    # --------------------------------------------------
    # Meter Bridge
    # --------------------------------------------------

    def _layout_meter_bridge(self, topology: Dict) -> Dict:
        u = self.UNIT

        net_positions = {
            "A": {"x": 0, "y": 0},
            "J": {"x": u * 3, "y": 0},
            "B": {"x": u * 3, "y": -u * 2},
            "C": {"x": u * 6, "y": 0}
        }

        placements = {}
        for cid, cdata in topology["components"].items():
            nfrom = cdata.get("from")
            nto = cdata.get("to")
            if nfrom in net_positions and nto in net_positions:
                p1 = net_positions[nfrom]
                p2 = net_positions[nto]
                placements[cid] = {
                    "x": (p1["x"] + p2["x"]) / 2,
                    "y": (p1["y"] + p2["y"]) / 2,
                    "type": cdata["type"],
                    "from": nfrom,
                    "to": nto
                }

        return {
            "layout_type": "meter_bridge",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": self._compute_bounds(net_positions, placements)
        }

    def _compute_bounds(self, net_positions: Dict, placements: Dict) -> Dict:
        all_points = list(net_positions.values())
        for v in placements.values():
            if "x" in v and "y" in v:
                all_points.append(v)

        if not all_points:
            return {"width": 0, "height": 0, "min_x": 0, "min_y": 0}

        min_x = min(p["x"] for p in all_points)
        max_x = max(p["x"] for p in all_points)
        min_y = min(p["y"] for p in all_points)
        max_y = max(p["y"] for p in all_points)

        return {
            "width": max_x - min_x + self.UNIT,
            "height": max_y - min_y + self.UNIT,
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y
        }


if __name__ == "__main__":
    import json

    from circuit_topology import CircuitTopology

    with open("circuit_blueprints.json", "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    topologist = CircuitTopology()
    engine = CircuitLayout()

    print("\nCIRCUIT LAYOUT REPORT\n")

    for bp in blueprints:
        topology = topologist.build(bp)
        layout = engine.generate(topology, bp)
        print("=" * 60)
        print(f"{bp['question_id']} ({bp['circuit_type']})")
        print(f"  Type: {layout['layout_type']}")
        print(f"  Node positions: {layout['net_positions']}")
        print(f"  Component placements: {layout['component_placements']}")
