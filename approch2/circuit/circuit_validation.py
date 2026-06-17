from typing import Dict, List

from circuit_rules import (
    COMPONENT_TYPES,
    CIRCUIT_TYPES
)


class CircuitValidation:

    def validate(self, blueprint: Dict) -> Dict:
        errors = []

        errors.extend(self._validate_top_level(blueprint))

        if errors:
            return {"valid": False, "errors": errors}

        errors.extend(self._validate_nodes(blueprint))
        errors.extend(self._validate_components(blueprint))

        return {"valid": len(errors) == 0, "errors": errors}

    def _validate_top_level(self, bp: Dict) -> List[str]:
        required = [
            "question_id",
            "renderer_type",
            "diagram_family",
            "circuit_type",
            "nodes",
            "components"
        ]

        errors = []
        for field in required:
            if field not in bp:
                errors.append(f"Missing top-level field: {field}")

        if bp.get("renderer_type") != "circuit":
            errors.append("renderer_type must be 'circuit'")

        ct = bp.get("circuit_type")
        if ct is not None and ct not in CIRCUIT_TYPES:
            errors.append(f"Unsupported circuit_type: {ct}")

        return errors

    def _validate_nodes(self, bp: Dict) -> List[str]:
        errors = []
        nodes = bp.get("nodes", [])

        if not nodes:
            errors.append("At least one node is required")
            return errors

        if len(nodes) != len(set(nodes)):
            seen = set()
            for nid in nodes:
                if nid in seen:
                    errors.append(f"Duplicate node: {nid}")
                seen.add(nid)

        return errors

    def _validate_components(self, bp: Dict) -> List[str]:
        errors = []
        components = bp.get("components", [])
        nodes = bp.get("nodes", [])

        if not components:
            errors.append("At least one component is required")
            return errors

        comp_ids = set()
        node_set = set(nodes)

        for comp in components:
            comp_id = comp.get("id")
            comp_type = comp.get("type")
            comp_from = comp.get("from")
            comp_to = comp.get("to")

            if not comp_id:
                errors.append("Component missing 'id'")
                continue

            if comp_id in comp_ids:
                errors.append(f"Duplicate component id: {comp_id}")
            comp_ids.add(comp_id)

            if not comp_type:
                errors.append(f"{comp_id}: missing 'type'")
            elif comp_type not in COMPONENT_TYPES:
                errors.append(f"{comp_id}: unsupported type '{comp_type}'")

            if not comp_from:
                errors.append(f"{comp_id}: missing 'from'")
            elif comp_from not in node_set:
                errors.append(f"{comp_id}: 'from' node '{comp_from}' not in nodes list")

            if not comp_to:
                errors.append(f"{comp_id}: missing 'to'")
            elif comp_to not in node_set:
                errors.append(f"{comp_id}: 'to' node '{comp_to}' not in nodes list")

            if comp_type == "resistor" and comp_type in COMPONENT_TYPES:
                val = comp.get("resistance")
                if val is not None and (not isinstance(val, (int, float)) or val <= 0):
                    errors.append(f"{comp_id}: resistance must be a positive number")

            if comp_type in ("battery", "cell"):
                val = comp.get("voltage")
                if val is not None and (not isinstance(val, (int, float)) or val <= 0):
                    errors.append(f"{comp_id}: voltage must be a positive number")

        return errors


if __name__ == "__main__":
    import json

    with open("circuit_blueprints.json", "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    validator = CircuitValidation()

    print("\nCIRCUIT VALIDATION REPORT\n")

    for bp in blueprints:
        result = validator.validate(bp)
        print("=" * 60)
        print(bp["question_id"], f"({bp['circuit_type']})")
        print("VALID :", result["valid"])
        if result["errors"]:
            for err in result["errors"]:
                print("  -", err)
        else:
            print("  PASS")
