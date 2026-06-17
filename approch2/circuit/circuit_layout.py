import math
from typing import Dict


class CircuitLayout:

    UNIT = 40

    def generate(self, topology: Dict, blueprint: Dict) -> Dict:
        circuit_type = topology["circuit_type"]
        nets = topology["nets"]
        components = topology["components"]

        if circuit_type in {
            "simple_series",
            "series_resistors",
            "three_resistor_series",
            "ammeter_series",
            "cell_key_bulb"
        }:
            return self._layout_series(nets, components, blueprint)

        elif circuit_type in {
            "parallel_resistors",
            "three_parallel",
            "voltmeter_parallel"
        }:
            return self._layout_parallel(nets, components, blueprint)

        elif circuit_type == "wheatstone_bridge":
            return self._layout_bridge(nets, components, blueprint)

        elif circuit_type == "meter_bridge":
            return self._layout_meter_bridge(nets, components, blueprint)

        raise ValueError(f"Unsupported circuit type: {circuit_type}")

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _net_center(self, net_id: str, net_positions: Dict) -> Dict:
        return net_positions.get(net_id, {"x": 0, "y": 0})

    def _place_component_between(
        self,
        comp_id: str,
        comp_data: Dict,
        net_a_pos: Dict,
        net_b_pos: Dict
    ) -> Dict:
        x1, y1 = net_a_pos["x"], net_a_pos["y"]
        x2, y2 = net_b_pos["x"], net_b_pos["y"]

        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        dx = x2 - x1
        dy = y2 - y1
        angle = math.degrees(math.atan2(dy, dx))

        return {
            "x": mid_x,
            "y": mid_y,
            "angle": angle,
            "length": math.sqrt(dx * dx + dy * dy),
            "type": comp_data["type"]
        }

    # --------------------------------------------------
    # Series layout
    # --------------------------------------------------

    def _layout_series(
        self,
        nets: Dict,
        components: Dict,
        blueprint: Dict
    ) -> Dict:
        u = self.UNIT
        ordered_nets = self._order_series_nets(nets, components)
        net_positions = {}
        x = 0

        for nid in ordered_nets:
            net_positions[nid] = {"x": x, "y": 0}
            x += u

        placements = {}
        for comp_id, comp_data in components.items():
            comp_nets = comp_data["connected_nets"]
            if len(comp_nets) == 2:
                pos_a = net_positions[comp_nets[0]]
                pos_b = net_positions[comp_nets[1]]
                placements[comp_id] = self._place_component_between(
                    comp_id, comp_data, pos_a, pos_b
                )

        self._add_wire_segments(net_positions, placements, nets, components)

        return {
            "layout_type": "series",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": self._compute_bounds(net_positions, placements)
        }

    def _order_series_nets(
        self,
        nets: Dict,
        components: Dict
    ) -> list:
        net_ids = list(nets.keys())
        if not net_ids:
            return []

        adj = {nid: [] for nid in net_ids}
        for comp_id, comp_data in components.items():
            comp_nets = comp_data["connected_nets"]
            if len(comp_nets) == 2:
                adj[comp_nets[0]].append(comp_nets[1])
                adj[comp_nets[1]].append(comp_nets[0])

        visited = set()
        order = []

        def dfs(nid):
            if nid in visited:
                return
            visited.add(nid)
            order.append(nid)
            for neighbor in adj[nid]:
                dfs(neighbor)

        dfs(net_ids[0])
        return order

    # --------------------------------------------------
    # Parallel layout
    # --------------------------------------------------

    def _layout_parallel(
        self,
        nets: Dict,
        components: Dict,
        blueprint: Dict
    ) -> Dict:
        u = self.UNIT
        net_ids = list(nets.keys())

        if len(net_ids) < 2:
            return {
                "layout_type": "parallel",
                "net_positions": {},
                "component_placements": {},
                "bounds": {"width": 0, "height": 0}
            }

        n0 = net_ids[0]
        n1 = net_ids[1]

        offset = u * 2
        net_positions = {
            n0: {"x": 0, "y": -offset},
            n1: {"x": 0, "y": offset}
        }

        parallel_comps = [
            cid for cid, cdata in components.items()
            if cdata["type"] not in ("battery", "cell")
        ]

        active_comps = [
            cid for cid, cdata in components.items()
            if cdata["type"] in ("battery", "cell")
        ]

        branch_index = 0
        placements = {}

        for cid in active_comps:
            cdata = components[cid]
            comp_nets = cdata["connected_nets"]
            if len(comp_nets) == 2:
                pas = net_positions[comp_nets[0]]
                pbs = net_positions[comp_nets[1]]
                mid_x = (pas["x"] + pbs["x"]) / 2 + branch_index * u
                placements[cid] = {
                    "x": mid_x,
                    "y": (pas["y"] + pbs["y"]) / 2,
                    "type": cdata["type"]
                }

        for cid in parallel_comps:
            cdata = components[cid]
            comp_nets = cdata["connected_nets"]
            if len(comp_nets) == 2:
                pas = net_positions[comp_nets[0]]
                pbs = net_positions[comp_nets[1]]
                bx = (branch_index + 1) * u * 1.5
                placements[cid] = {
                    "x": bx,
                    "y": (pas["y"] + pbs["y"]) / 2,
                    "type": cdata["type"]
                }
                branch_index += 1

        self._add_wire_segments(net_positions, placements, nets, components)

        return {
            "layout_type": "parallel",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": self._compute_bounds(net_positions, placements)
        }

    # --------------------------------------------------
    # Bridge layout (Wheatstone)
    # --------------------------------------------------

    def _layout_bridge(
        self,
        nets: Dict,
        components: Dict,
        blueprint: Dict
    ) -> Dict:
        u = self.UNIT
        net_ids = list(nets.keys())

        lookup = {nid: i for i, nid in enumerate(net_ids)}

        positions_2d = {
            "N0": {"x": 0, "y": -u * 2},
            "N1": {"x": -u * 2, "y": 0},
            "N2": {"x": u * 2, "y": 0},
            "N3": {"x": 0, "y": u * 2}
        }

        net_positions = {}
        for nid in net_ids:
            if nid in positions_2d:
                net_positions[nid] = positions_2d[nid]
            else:
                net_positions[nid] = {"x": 0, "y": 0}

        placements = {}
        bridge_center_x = 0
        bridge_center_y = 0

        for comp_id, comp_data in components.items():
            comp_nets = comp_data["connected_nets"]
            if len(comp_nets) == 2:
                pas = net_positions.get(comp_nets[0], {"x": 0, "y": 0})
                pbs = net_positions.get(comp_nets[1], {"x": 0, "y": 0})
                placements[comp_id] = self._place_component_between(
                    comp_id, comp_data, pas, pbs
                )

        g1_data = components.get("G1")
        if g1_data:
            placements["G1"] = {
                "x": bridge_center_x,
                "y": bridge_center_y,
                "angle": 90,
                "type": "galvanometer"
            }

        return {
            "layout_type": "bridge",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": self._compute_bounds(net_positions, placements)
        }

    # --------------------------------------------------
    # Meter bridge layout
    # --------------------------------------------------

    def _layout_meter_bridge(
        self,
        nets: Dict,
        components: Dict,
        blueprint: Dict
    ) -> Dict:
        u = self.UNIT

        net_positions = {
            "A": {"x": 0, "y": 0},
            "J": {"x": u * 3, "y": 0},
            "M": {"x": u * 3, "y": -u * 2},
            "B": {"x": u * 6, "y": 0}
        }

        placements = {}
        for comp_id, comp_data in components.items():
            comp_nets = comp_data["connected_nets"]
            if len(comp_nets) == 2:
                pas = net_positions.get(comp_nets[0], {"x": 0, "y": 0})
                pbs = net_positions.get(comp_nets[1], {"x": 0, "y": 0})
                placements[comp_id] = self._place_component_between(
                    comp_id, comp_data, pas, pbs
                )

        return {
            "layout_type": "meter_bridge",
            "net_positions": net_positions,
            "component_placements": placements,
            "bounds": self._compute_bounds(net_positions, placements)
        }

    # --------------------------------------------------
    # Wire segments
    # --------------------------------------------------

    def _add_wire_segments(
        self,
        net_positions: Dict,
        placements: Dict,
        nets: Dict,
        components: Dict
    ) -> None:
        pass

    # --------------------------------------------------
    # Bounds
    # --------------------------------------------------

    def _compute_bounds(
        self,
        net_positions: Dict,
        placements: Dict
    ) -> Dict:
        all_points = list(net_positions.values()) + [
            v for v in placements.values()
            if "x" in v and "y" in v
        ]

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
    layout_engine = CircuitLayout()

    print("\nCIRCUIT LAYOUT REPORT\n")

    for bp in blueprints:
        topology = topologist.build(bp)
        layout = layout_engine.generate(topology, bp)
        print("=" * 60)
        print(bp["question_id"], f"({bp['circuit_type']})")
        print(f"  Layout type: {layout['layout_type']}")
        print(f"  Net positions: {layout['net_positions']}")
        print(f"  Component placements: {layout['component_placements']}")
        print(f"  Bounds: {layout['bounds']}")
