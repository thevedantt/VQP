from typing import Dict, List

from circuit_rules import (
    COMPONENT_TYPES,
    CIRCUIT_TYPES,
    REQUIRED_TERMINAL_COUNT,
    TERMINAL_ROLES,
    ANNOTATION_TYPES
)


class CircuitValidation:

    def validate(self, blueprint: Dict) -> Dict:
        errors = []

        errors.extend(self._validate_top_level(blueprint))

        if errors:
            return {"valid": False, "errors": errors}

        errors.extend(self._validate_nets(blueprint))
        errors.extend(self._validate_components(blueprint))
        errors.extend(self._validate_terminals(blueprint))
        errors.extend(self._validate_annotations(blueprint))

        return {"valid": len(errors) == 0, "errors": errors}

    # --------------------------------------------------
    # Top-level schema
    # --------------------------------------------------

    def _validate_top_level(self, bp: Dict) -> List[str]:
        required = [
            "schema_version",
            "question_id",
            "renderer_type",
            "diagram_family",
            "circuit_type",
            "nets",
            "components"
        ]

        errors = []

        for field in required:
            if field not in bp:
                errors.append(f"Missing top-level field: {field}")

        if bp.get("renderer_type") != "circuit":
            errors.append("renderer_type must be 'circuit'")

        if bp.get("schema_version") != "2.0":
            errors.append("schema_version must be 2.0")

        ct = bp.get("circuit_type")
        if ct is not None and ct not in CIRCUIT_TYPES:
            errors.append(f"Unsupported circuit_type: {ct}")

        return errors

    # --------------------------------------------------
    # Nets
    # --------------------------------------------------

    def _validate_nets(self, bp: Dict) -> List[str]:
        errors = []
        nets = bp.get("nets", [])

        if not nets:
            errors.append("At least one net is required")
            return errors

        net_ids = set()

        for net in nets:
            nid = net.get("id")
            if not nid:
                errors.append("Net missing id")
                continue
            if nid in net_ids:
                errors.append(f"Duplicate net id: {nid}")
            net_ids.add(nid)

        return errors

    # --------------------------------------------------
    # Components
    # --------------------------------------------------

    def _validate_components(self, bp: Dict) -> List[str]:
        errors = []
        components = bp.get("components", [])

        if not components:
            errors.append("At least one component is required")
            return errors

        comp_ids = set()
        net_ids = {n["id"] for n in bp.get("nets", [])}

        for comp in components:
            comp_id = comp.get("id")
            comp_type = comp.get("type")

            if not comp_id:
                errors.append("Component missing id")
                continue

            if comp_id in comp_ids:
                errors.append(f"Duplicate component id: {comp_id}")
            comp_ids.add(comp_id)

            if comp_type not in COMPONENT_TYPES:
                errors.append(f"Unsupported component type: {comp_type}")
                continue

            expected_terminals = REQUIRED_TERMINAL_COUNT.get(comp_type, 0)
            terminals = comp.get("terminals", [])

            if len(terminals) != expected_terminals:
                errors.append(
                    f"{comp_id}: expected {expected_terminals} terminals, "
                    f"got {len(terminals)}"
                )

            terminal_ids = set()
            for term in terminals:
                tid = term.get("id")
                tnet = term.get("net")
                if not tid:
                    errors.append(f"{comp_id}: terminal missing id")
                else:
                    if tid in terminal_ids:
                        errors.append(f"{comp_id}: duplicate terminal id {tid}")
                    terminal_ids.add(tid)
                if tnet is not None and tnet not in net_ids:
                    errors.append(f"{comp_id}.{tid}: references unknown net '{tnet}'")

            if comp_type == "resistor" and comp_type in COMPONENT_TYPES:
                value = comp.get("value")
                if value is not None and (not isinstance(value, (int, float)) or value <= 0):
                    errors.append(f"{comp_id}: resistor value must be a positive number")

            if comp_type in ("battery", "cell"):
                value = comp.get("value")
                if value is not None and (not isinstance(value, (int, float)) or value <= 0):
                    errors.append(f"{comp_id}: voltage must be a positive number")

        return errors

    # --------------------------------------------------
    # Terminal cross-check
    # --------------------------------------------------

    def _validate_terminals(self, bp: Dict) -> List[str]:
        errors = []
        net_ids = {n["id"] for n in bp.get("nets", [])}

        for comp in bp.get("components", []):
            comp_type = comp.get("type")
            roles = TERMINAL_ROLES.get(comp_type, [])
            if roles:
                assigned_roles = []
                for term in comp.get("terminals", []):
                    role = term.get("role")
                    if role:
                        assigned_roles.append(role)
                for expected_role in roles:
                    if expected_role not in assigned_roles:
                        errors.append(
                            f"{comp['id']}: missing terminal role '{expected_role}'"
                        )

            for term in comp.get("terminals", []):
                tnet = term.get("net")
                if tnet is not None and tnet not in net_ids:
                    errors.append(
                        f"{comp['id']}.{term.get('id', '?')}: "
                        f"net '{tnet}' not found"
                    )

        return errors

    # --------------------------------------------------
    # Annotations
    # --------------------------------------------------

    def _validate_annotations(self, bp: Dict) -> List[str]:
        errors = []
        comp_ids = {c["id"] for c in bp.get("components", [])}

        for ann in bp.get("annotations", []):
            ann_id = ann.get("id")
            ann_type = ann.get("type")
            if not ann_id:
                errors.append("Annotation missing id")
            if ann_type and ann_type not in ANNOTATION_TYPES:
                errors.append(f"Unsupported annotation type: {ann_type}")
            target = ann.get("target_component")
            if target and target not in comp_ids:
                errors.append(f"Annotation targets unknown component: {target}")

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
        print(bp["question_id"], f"(v{bp.get('schema_version', '?')})")
        print("VALID :", result["valid"])
        if result["errors"]:
            for err in result["errors"]:
                print("  -", err)
        else:
            print("  PASS")
