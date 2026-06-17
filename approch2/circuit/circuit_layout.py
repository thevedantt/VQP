"""
circuit_layout.py

Schema V2 layout engine.
Responsibility: topology → deterministic coordinates.
Does NOT validate, does NOT solve, does NOT render.
"""

from typing import Dict, List, Tuple

from circuit_rules import SERIES_CIRCUITS, PARALLEL_CIRCUITS


class CircuitLayout:

    UNIT: int = 40

    def generate(self, topology: Dict, blueprint: Dict) -> Dict:
        circuit_type = topology["circuit_type"]

        if circuit_type in SERIES_CIRCUITS:
            return self._layout_series(topology)
        elif circuit_type in PARALLEL_CIRCUITS:
            return self._layout_parallel(topology)
        elif circuit_type == "wheatstone_bridge":
            return self._layout_bridge(topology)
        elif circuit_type == "meter_bridge":
            return self._layout_meter_bridge(topology)

        raise ValueError(f"Unsupported circuit type: {circuit_type}")

    # ==========================================================
    # SERIES
    # ==========================================================

    def _layout_series(self, topology: Dict) -> Dict:
        u = self.UNIT
        node_order = topology["node_order"]
        components = topology["components"]

        net_positions: Dict[str, Dict] = {}
        x = 0
        for nid in node_order:
            net_positions[nid] = {"x": x, "y": 0}
            x += u

        placements: Dict[str, Dict] = {}
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

        bounds = self._compute_bounds(net_positions, placements)

        return {
            "layout_type": "series",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": bounds
        }

    # ==========================================================
    # PARALLEL
    # ==========================================================

    def _layout_parallel(self, topology: Dict) -> Dict:
        u = self.UNIT
        nodes = topology["nodes"]
        components = topology["components"]

        if len(nodes) < 2:
            return {
                "layout_type": "parallel",
                "net_positions": {},
                "component_placements": {},
                "bounds": {"width": 0, "height": 0, "min_x": 0, "min_y": 0}
            }

        n0, n1 = nodes[0], nodes[1]
        offset = u * 2

        net_positions: Dict[str, Dict] = {
            n0: {"x": 0, "y": -offset},
            n1: {"x": 0, "y": offset}
        }

        # Separate source (battery/cell) from passive/measuring components
        sources: List[str] = []
        branches: List[str] = []
        for cid, cdata in components.items():
            if cdata["type"] in ("battery", "cell"):
                sources.append(cid)
            else:
                branches.append(cid)

        placements: Dict[str, Dict] = {}

        # Source at center-left
        for i, cid in enumerate(sources):
            placements[cid] = {
                "x": 0,
                "y": 0,
                "type": components[cid]["type"]
            }

        # Branches spread horizontally from the source
        for i, cid in enumerate(branches):
            placements[cid] = {
                "x": (i + 1) * u * 1.5,
                "y": 0,
                "type": components[cid]["type"]
            }

        bounds = self._compute_bounds(net_positions, placements)

        return {
            "layout_type": "parallel",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": bounds
        }

    # ==========================================================
    # WHEATSTONE BRIDGE
    # ==========================================================

    def _layout_bridge(self, topology: Dict) -> Dict:
        u = self.UNIT
        nodes = topology["nodes"]
        components = topology["components"]

        # Standard diamond layout
        anchor: Dict[str, Tuple[float, float]] = {
            "A": (0, -u * 2),      # top
            "B": (-u * 2, 0),      # left
            "C": (u * 2, 0),       # right
            "D": (0, u * 2)        # bottom
        }

        net_positions: Dict[str, Dict] = {}
        for nid in nodes:
            pos = anchor.get(nid, (0, 0))
            net_positions[nid] = {"x": pos[0], "y": pos[1]}

        placements: Dict[str, Dict] = {}
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

        if "G" in components:
            placements["G"] = {
                "x": 0, "y": 0,
                "type": "galvanometer",
                "from": "B",
                "to": "C"
            }

        bounds = self._compute_bounds(net_positions, placements)

        return {
            "layout_type": "bridge",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": bounds
        }

    # ==========================================================
    # METER BRIDGE
    # ==========================================================

    def _layout_meter_bridge(self, topology: Dict) -> Dict:
        u = self.UNIT

        # A---J---C  (100cm wire split at jockey J)
        #  \  |
        #   \ |
        #    B
        net_positions: Dict[str, Dict] = {
            "A": {"x": 0, "y": 0},
            "J": {"x": u * 3, "y": 0},
            "B": {"x": u * 3, "y": -u * 2},
            "C": {"x": u * 6, "y": 0}
        }

        placements: Dict[str, Dict] = {}
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

        bounds = self._compute_bounds(net_positions, placements)

        return {
            "layout_type": "meter_bridge",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": bounds
        }

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _compute_bounds(
        self,
        net_positions: Dict[str, Dict],
        placements: Dict[str, Dict]
    ) -> Dict[str, float]:
        all_pts: List[Dict] = list(net_positions.values())
        for v in placements.values():
            if "x" in v and "y" in v:
                all_pts.append(v)

        if not all_pts:
            return {"width": 0, "height": 0, "min_x": 0, "min_y": 0}

        min_x = min(p["x"] for p in all_pts)
        max_x = max(p["x"] for p in all_pts)
        min_y = min(p["y"] for p in all_pts)
        max_y = max(p["y"] for p in all_pts)

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

    print("=" * 64)
    print("  CIRCUIT LAYOUT REPORT")
    print("=" * 64)

    for bp in blueprints:
        topology = topologist.build(bp)
        layout = engine.generate(topology, bp)
        qid = bp.get("question_id", "?")
        ct = bp.get("circuit_type", "?")
        lt = layout["layout_type"]
        print(f"\n  {qid} ({ct}) -> {lt}")
        print(f"  Nets: {layout['net_positions']}")
        print(f"  Components: {layout['component_placements']}")
        print(f"  Bounds: {layout['bounds']}")

    print(f"\n{'=' * 64}")
    print("  LAYOUT GENERATION COMPLETE")
    print(f"{'=' * 64}")
