from typing import Dict, List


class CircuitTopology:

    def build(self, blueprint: Dict) -> Dict:
        nodes = blueprint["nodes"]
        components_raw = blueprint["components"]

        adjacency = {nid: [] for nid in nodes}
        components = {}

        for comp in components_raw:
            cid = comp["id"]
            ctype = comp["type"]
            cfrom = comp.get("from")
            cto = comp.get("to")

            comp_entry = {
                "id": cid,
                "type": ctype,
                "from": cfrom,
                "to": cto
            }

            for attr in ("voltage", "resistance", "length_cm", "state", "label"):
                if attr in comp:
                    comp_entry[attr] = comp[attr]

            components[cid] = comp_entry

            if cfrom in adjacency:
                adjacency[cfrom].append(cid)
            if cto in adjacency:
                adjacency[cto].append(cid)

        net_connectivity = {}
        for comp in components_raw:
            cid = comp["id"]
            cfrom = comp.get("from")
            cto = comp.get("to")
            if cfrom and cto:
                key = frozenset([cfrom, cto])
                if key not in net_connectivity:
                    net_connectivity[key] = []
                net_connectivity[key].append(cid)

        parallel_groups = []
        for (n1, n2), comps in net_connectivity.items():
            if len(comps) > 1:
                parallel_groups.append({
                    "nodes": [n1, n2] if not isinstance(n1, str) else list({n1, n2}),
                    "component_ids": comps
                })

        node_order = self._order_nodes(nodes, adjacency, components)

        return {
            "circuit_type": blueprint["circuit_type"],
            "question_id": blueprint["question_id"],
            "nodes": nodes,
            "components": components,
            "adjacency": adjacency,
            "node_order": node_order,
            "parallel_groups": parallel_groups,
            "node_count": len(nodes),
            "component_count": len(components)
        }

    def _order_nodes(self, nodes: List[str], adjacency: Dict, components: Dict) -> List[str]:
        if not nodes:
            return []

        def neighbors(nid):
            result = []
            for comp_id in adjacency.get(nid, []):
                comp = components.get(comp_id)
                if comp:
                    other = comp["to"] if comp["from"] == nid else comp["from"]
                    if other and other in adjacency:
                        result.append(other)
            return result

        visited = set()
        order = []

        def dfs(nid):
            if nid in visited:
                return
            visited.add(nid)
            order.append(nid)
            for nb in neighbors(nid):
                dfs(nb)

        for nid in nodes:
            if nid not in visited:
                dfs(nid)

        return order


if __name__ == "__main__":
    import json

    with open("circuit_blueprints.json", "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    topology = CircuitTopology()

    print("\nCIRCUIT TOPOLOGY REPORT\n")

    for bp in blueprints:
        result = topology.build(bp)
        print("=" * 60)
        print(f"{result['question_id']} ({result['circuit_type']})")
        print(f"  Nodes: {result['node_count']}, Components: {result['component_count']}")
        print(f"  Node order: {result['node_order']}")
        print(f"  Components:")
        for cid, cdata in result["components"].items():
            print(f"    {cid}: {cdata['type']} {cdata['from']}->{cdata['to']}")
        if result["parallel_groups"]:
            print(f"  Parallel groups: {result['parallel_groups']}")
