from typing import Dict


class CircuitTopology:

    def build(self, blueprint: Dict) -> Dict:
        nets = {n["id"]: {"id": n["id"], "components": []} for n in blueprint["nets"]}
        components = {}

        for comp in blueprint["components"]:
            comp_id = comp["id"]
            comp_entry = {
                "id": comp_id,
                "type": comp["type"],
                "value": comp.get("value"),
                "units": comp.get("units"),
                "terminals": [],
                "connected_nets": set()
            }

            for term in comp["terminals"]:
                net_id = term["net"]
                comp_entry["terminals"].append({
                    "id": term["id"],
                    "net": net_id,
                    "role": term.get("role")
                })
                comp_entry["connected_nets"].add(net_id)

                if net_id in nets:
                    nets[net_id]["components"].append({
                        "component_id": comp_id,
                        "terminal_id": term["id"],
                        "role": term.get("role")
                    })

            comp_entry["connected_nets"] = sorted(comp_entry["connected_nets"])
            components[comp_id] = comp_entry

        adjacency_list = {}
        for net_id, net_data in nets.items():
            adjacency_list[net_id] = {
                "component_ids": list(set(
                    c["component_id"] for c in net_data["components"]
                ))
            }

        for comp_id, comp_data in components.items():
            adjacency_list[comp_id] = {
                "net_ids": comp_data["connected_nets"]
            }

        circuit_type = blueprint["circuit_type"]

        return {
            "circuit_type": circuit_type,
            "question_id": blueprint["question_id"],
            "nets": nets,
            "components": components,
            "adjacency_list": adjacency_list,
            "net_count": len(nets),
            "component_count": len(components),
            "topology_classification": self._classify_topology(
                nets, components, circuit_type
            )
        }

    def _classify_topology(
        self,
        nets: Dict,
        components: Dict,
        circuit_type: str
    ) -> Dict:
        component_count = len(components)
        net_count = len(nets)
        parallel_groups = []
        series_chains = []

        net_to_comps = {}
        for nid, ndata in nets.items():
            comp_ids = list(set(c["component_id"] for c in ndata["components"]))
            if comp_ids:
                net_to_comps[nid] = comp_ids

        comp_pairs = {}
        for nid, comp_ids in net_to_comps.items():
            if len(comp_ids) >= 2:
                for i in range(len(comp_ids)):
                    for j in range(i + 1, len(comp_ids)):
                        pair = tuple(sorted([comp_ids[i], comp_ids[j]]))
                        if pair not in comp_pairs:
                            comp_pairs[pair] = []
                        comp_pairs[pair].append(nid)

        for pair, shared_nets in comp_pairs.items():
            if len(shared_nets) >= 2:
                parallel_groups.append({
                    "components": list(pair),
                    "shared_nets": shared_nets
                })

        for comp_id, comp_data in components.items():
            comp_nets = comp_data["connected_nets"]
            if len(comp_nets) == 2:
                series_chains.append({
                    "component_id": comp_id,
                    "net_a": comp_nets[0],
                    "net_b": comp_nets[1]
                })

        return {
            "parallel_groups": parallel_groups,
            "series_connections": series_chains,
            "component_count": component_count,
            "net_count": net_count
        }


if __name__ == "__main__":
    import json

    with open("circuit_blueprints.json", "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    topology = CircuitTopology()

    print("\nCIRCUIT TOPOLOGY REPORT\n")

    for bp in blueprints:
        result = topology.build(bp)
        print("=" * 60)
        print(result["question_id"], f"({result['circuit_type']})")
        print(f"  Nets: {result['net_count']}, Components: {result['component_count']}")
        print(f"  Topology: {result['topology_classification']}")
        print(f"  Adjacency: {result['adjacency_list']}")
