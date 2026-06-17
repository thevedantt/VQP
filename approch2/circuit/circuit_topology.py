"""
circuit_topology.py

Schema V2 topology builder.
Responsibility: convert nodes + components → graph representation.
Does NOT validate, does NOT solve, does NOT render.
"""

from typing import Dict, List


class CircuitTopology:

    def build(self, blueprint: Dict) -> Dict:
        nodes: List[str] = list(blueprint.get("nodes", []))
        components_raw: List[Dict] = list(blueprint.get("components", []))

        # --- adjacency: node → [component ids] ---
        adjacency: Dict[str, List[str]] = {nid: [] for nid in nodes}

        # --- component registry ---
        components: Dict[str, Dict] = {}

        for comp in components_raw:
            cid = comp["id"]
            ctype = comp["type"]
            cfrom = comp.get("from", "")
            cto = comp.get("to", "")

            entry: Dict = {
                "id": cid,
                "type": ctype,
                "from": cfrom,
                "to": cto,
            }

            # forward relevant optional fields
            for attr in ("voltage", "resistance", "length_cm", "state", "label", "current"):
                if attr in comp:
                    entry[attr] = comp[attr]

            components[cid] = entry

            if cfrom in adjacency:
                adjacency[cfrom].append(cid)
            if cto in adjacency:
                adjacency[cto].append(cid)

        # --- node ordering (DFS traversal) ---
        node_order: List[str] = self._order_nodes(nodes, adjacency, components)

        # --- parallel group detection ---
        parallel_groups = self._detect_parallel_groups(components)

        # --- circuit edges (component → node pair) ---
        edges: List[Dict] = []
        for cid, cdata in components.items():
            edges.append({
                "component_id": cid,
                "type": cdata["type"],
                "from": cdata["from"],
                "to": cdata["to"]
            })

        return {
            "question_id": blueprint.get("question_id", "?"),
            "circuit_type": blueprint.get("circuit_type", "?"),
            "nodes": nodes,
            "components": components,
            "adjacency": adjacency,
            "node_order": node_order,
            "parallel_groups": parallel_groups,
            "edges": edges,
            "node_count": len(nodes),
            "component_count": len(components)
        }

    # --------------------------------------------------
    # DFS node ordering
    # --------------------------------------------------

    def _order_nodes(
        self,
        nodes: List[str],
        adjacency: Dict[str, List[str]],
        components: Dict[str, Dict]
    ) -> List[str]:
        if not nodes:
            return []

        def _neighbors(nid: str) -> List[str]:
            result: List[str] = []
            for comp_id in adjacency.get(nid, []):
                comp = components.get(comp_id)
                if comp:
                    other = comp["to"] if comp["from"] == nid else comp["from"]
                    if other and other in adjacency:
                        result.append(other)
            return result

        visited: set = set()
        order: List[str] = []

        def _dfs(nid: str) -> None:
            if nid in visited:
                return
            visited.add(nid)
            order.append(nid)
            for nb in _neighbors(nid):
                _dfs(nb)

        for nid in nodes:
            if nid not in visited:
                _dfs(nid)

        return order

    # --------------------------------------------------
    # Parallel group detection
    # --------------------------------------------------

    def _detect_parallel_groups(self, components: Dict[str, Dict]) -> List[Dict]:
        net_pairs: Dict[frozenset, List[str]] = {}

        for cid, cdata in components.items():
            cfrom = cdata.get("from")
            cto = cdata.get("to")
            if cfrom and cto:
                key = frozenset([cfrom, cto])
                if key not in net_pairs:
                    net_pairs[key] = []
                net_pairs[key].append(cid)

        groups: List[Dict] = []
        for pair, comps in net_pairs.items():
            if len(comps) > 1:
                groups.append({
                    "nodes": sorted(pair),
                    "component_ids": comps,
                    "component_count": len(comps)
                })

        return groups


if __name__ == "__main__":
    import json

    with open("circuit_blueprints.json", "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    topologist = CircuitTopology()

    print("=" * 64)
    print("  CIRCUIT TOPOLOGY REPORT")
    print("=" * 64)

    for bp in blueprints:
        result = topologist.build(bp)
        qid = result["question_id"]
        ct = result["circuit_type"]
        print(f"\n  {qid} ({ct})")
        print(f"  Nodes: {result['node_count']}, Components: {result['component_count']}")
        print(f"  Order: {result['node_order']}")
        for cid, cdata in result["components"].items():
            print(f"    {cid}: {cdata['type']}  {cdata['from']} -> {cdata['to']}")
        if result["parallel_groups"]:
            print(f"  Parallel groups: {len(result['parallel_groups'])}")
            for g in result["parallel_groups"]:
                print(f"    {g['nodes']}: {g['component_ids']}")

    print(f"\n{'=' * 64}")
    print("  TOPOLOGY BUILD COMPLETE")
    print(f"{'=' * 64}")
