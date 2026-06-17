"""
circuit_validation.py

Schema V2 validation layer.
Responsibility: validate blueprint structure only.
Does NOT build topology, does NOT solve, does NOT render.
"""

from typing import Dict, List

from circuit_rules import (
    COMPONENT_TYPES,
    CIRCUIT_TYPES,
    COMPONENT_REQUIRED_FIELDS,
    COMPONENT_VALUE_FIELD
)


class CircuitValidation:

    def validate(self, blueprint: Dict) -> Dict:
        errors: List[str] = []

        errors.extend(self._validate_top_level(blueprint))

        if errors:
            return {"valid": False, "errors": errors}

        errors.extend(self._validate_nodes(blueprint))
        errors.extend(self._validate_components(blueprint))
        errors.extend(self._validate_node_references(blueprint))

        return {"valid": len(errors) == 0, "errors": errors}

    # --------------------------------------------------
    # Top-level structure
    # --------------------------------------------------

    def _validate_top_level(self, bp: Dict) -> List[str]:
        errors: List[str] = []

        if not isinstance(bp, dict):
            return ["Blueprint must be a JSON object"]

        required = [
            "question_id",
            "renderer_type",
            "diagram_family",
            "circuit_type",
            "nodes",
            "components"
        ]

        for field in required:
            if field not in bp:
                errors.append(f"Missing required top-level field: '{field}'")

        if errors:
            return errors

        if bp.get("renderer_type") != "circuit":
            errors.append(
                f"renderer_type must be 'circuit', got '{bp.get('renderer_type')}'"
            )

        ct = bp.get("circuit_type")
        if ct not in CIRCUIT_TYPES:
            errors.append(f"Unsupported circuit_type: '{ct}'")

        nodes = bp.get("nodes")
        if nodes is not None and not isinstance(nodes, list):
            errors.append("'nodes' must be a list")

        comps = bp.get("components")
        if comps is not None and not isinstance(comps, list):
            errors.append("'components' must be a list")

        return errors

    # --------------------------------------------------
    # Nodes
    # --------------------------------------------------

    def _validate_nodes(self, bp: Dict) -> List[str]:
        errors: List[str] = []
        nodes = bp.get("nodes", [])

        if len(nodes) < 2:
            errors.append(f"At least 2 nodes required, found {len(nodes)}")
            return errors

        seen: set = set()
        for i, nid in enumerate(nodes):
            if not isinstance(nid, str) or not nid.strip():
                errors.append(f"nodes[{i}]: each node must be a non-empty string")
                continue
            if nid in seen:
                errors.append(f"Duplicate node: '{nid}'")
            seen.add(nid)

        return errors

    # --------------------------------------------------
    # Components
    # --------------------------------------------------

    def _validate_components(self, bp: Dict) -> List[str]:
        errors: List[str] = []
        components = bp.get("components", [])
        nodes = bp.get("nodes", [])
        node_set = set(nodes)

        if not components:
            errors.append("At least one component is required")
            return errors

        comp_ids: set = set()

        for i, comp in enumerate(components):
            if not isinstance(comp, dict):
                errors.append(f"components[{i}]: must be a JSON object")
                continue

            cid = comp.get("id")
            ctype = comp.get("type")
            cfrom = comp.get("from")
            cto = comp.get("to")

            # --- id validation ---
            if not cid or not isinstance(cid, str):
                errors.append(f"components[{i}]: missing or invalid 'id'")
            else:
                if cid in comp_ids:
                    errors.append(f"Duplicate component id: '{cid}'")
                comp_ids.add(cid)

            # --- type validation ---
            if not ctype or not isinstance(ctype, str):
                errors.append(f"components[{i}] ('{cid}'): missing or invalid 'type'")
            elif ctype not in COMPONENT_TYPES:
                errors.append(f"'{cid}': unsupported type '{ctype}'")

            # --- from validation ---
            if not cfrom or not isinstance(cfrom, str):
                errors.append(f"'{cid}': missing or invalid 'from'")
            elif cfrom not in node_set:
                errors.append(f"'{cid}': 'from' node '{cfrom}' not found in nodes")

            # --- to validation ---
            if not cto or not isinstance(cto, str):
                errors.append(f"'{cid}': missing or invalid 'to'")
            elif cto not in node_set:
                errors.append(f"'{cid}': 'to' node '{cto}' not found in nodes")

            # --- self-loop check ---
            if cfrom and cto and cfrom == cto:
                errors.append(f"'{cid}': 'from' and 'to' must be different nodes")

            # --- value validation (positive numbers) ---
            if ctype in COMPONENT_TYPES:
                vf = COMPONENT_VALUE_FIELD.get(ctype)
                if vf:
                    val = comp.get(vf)
                    if val is not None:
                        if not isinstance(val, (int, float)):
                            errors.append(
                                f"'{cid}': {vf} must be a number, got {type(val).__name__}"
                            )
                        elif val <= 0:
                            errors.append(
                                f"'{cid}': {vf} must be positive, got {val}"
                            )

            # --- warn on unknown fields ---
            known_fields = {"id", "type", "from", "to", "state", "label", "current"}
            known_fields |= set(COMPONENT_VALUE_FIELD.values())
            for field in comp:
                if field not in known_fields and field not in COMPONENT_VALUE_FIELD.values():
                    errors.append(f"'{cid}': unknown field '{field}'")

        return errors

    # --------------------------------------------------
    # Node reference consistency
    # --------------------------------------------------

    def _validate_node_references(self, bp: Dict) -> List[str]:
        errors: List[str] = []
        nodes = bp.get("nodes", [])
        components = bp.get("components", [])

        referenced: set = set()
        for comp in components:
            cfrom = comp.get("from")
            cto = comp.get("to")
            if cfrom:
                referenced.add(cfrom)
            if cto:
                referenced.add(cto)

        for nid in nodes:
            if nid not in referenced:
                errors.append(f"Node '{nid}' is declared but never referenced by any component")

        return errors


if __name__ == "__main__":
    import json

    with open("circuit_blueprints.json", "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    validator = CircuitValidation()

    print("=" * 64)
    print("  CIRCUIT VALIDATION REPORT")
    print("=" * 64)

    all_pass = True
    for bp in blueprints:
        result = validator.validate(bp)
        qid = bp.get("question_id", "?")
        ct = bp.get("circuit_type", "?")
        status = "PASS" if result["valid"] else "FAIL"
        if not result["valid"]:
            all_pass = False
        print(f"\n  {qid} ({ct}): {status}")
        if result["errors"]:
            for err in result["errors"]:
                print(f"    - {err}")

    print(f"\n{'=' * 64}")
    print(f"  OVERALL: {'ALL VALID' if all_pass else 'VALIDATION FAILURES DETECTED'}")
    print(f"{'=' * 64}")
