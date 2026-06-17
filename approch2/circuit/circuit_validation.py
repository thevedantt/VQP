
from typing import Dict, List

from circuit_rules import (
    COMPONENT_TYPES,
    CIRCUIT_TYPES,
    REQUIRED_COMPONENTS
)


class CircuitValidation:

    def validate(self, blueprint: Dict) -> Dict:

        errors = []

        errors.extend(self._validate_schema(blueprint))

        if errors:
            return {
                "valid": False,
                "errors": errors
            }

        errors.extend(self._validate_circuit_type(blueprint))
        errors.extend(self._validate_components(blueprint))
        errors.extend(self._validate_connections(blueprint))
        errors.extend(self._validate_required_components(blueprint))

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    # --------------------------------------------------
    # Schema
    # --------------------------------------------------

    def _validate_schema(self, bp: Dict) -> List[str]:

        required = [
            "question_id",
            "renderer_type",
            "diagram_family",
            "circuit_type",
            "components",
            "connections"
        ]

        errors = []

        for field in required:
            if field not in bp:
                errors.append(
                    f"Missing field: {field}"
                )

        if bp.get("renderer_type") != "circuit":
            errors.append(
                "renderer_type must be circuit"
            )

        return errors

    # --------------------------------------------------
    # Circuit Type
    # --------------------------------------------------

    def _validate_circuit_type(self, bp: Dict):

        errors = []

        circuit_type = bp["circuit_type"]

        if circuit_type not in CIRCUIT_TYPES:
            errors.append(
                f"Unsupported circuit type: {circuit_type}"
            )

        return errors

    # --------------------------------------------------
    # Components
    # --------------------------------------------------

    def _validate_components(self, bp: Dict):

        errors = []

        components = bp["components"]

        ids = set()

        for comp in components:

            comp_id = comp.get("id")
            comp_type = comp.get("type")

            if not comp_id:
                errors.append(
                    "Component missing id"
                )
                continue

            if comp_id in ids:
                errors.append(
                    f"Duplicate component id: {comp_id}"
                )

            ids.add(comp_id)

            if comp_type not in COMPONENT_TYPES:
                errors.append(
                    f"Unsupported component type: {comp_type}"
                )

            if comp_type == "resistor":

                resistance = comp.get(
                    "resistance",
                    0
                )

                if resistance <= 0:
                    errors.append(
                        f"{comp_id}: resistance must be > 0"
                    )

            if comp_type in {"battery", "cell"}:

                voltage = comp.get(
                    "voltage",
                    0
                )

                if voltage <= 0:
                    errors.append(
                        f"{comp_id}: voltage must be > 0"
                    )

        return errors

    # --------------------------------------------------
    # Connections
    # --------------------------------------------------

    def _validate_connections(self, bp: Dict):

        errors = []

        components = bp["components"]

        valid_ids = {
            c["id"] for c in components
        }

        for connection in bp["connections"]:

            if len(connection) != 2:
                errors.append(
                    f"Invalid connection: {connection}"
                )
                continue

            a, b = connection

            if a not in valid_ids:
                errors.append(
                    f"Unknown component: {a}"
                )

            if b not in valid_ids:
                errors.append(
                    f"Unknown component: {b}"
                )

        return errors

    # --------------------------------------------------
    # Required Components
    # --------------------------------------------------

    def _validate_required_components(self, bp: Dict):

        errors = []

        circuit_type = bp["circuit_type"]

        required = REQUIRED_COMPONENTS.get(
            circuit_type,
            []
        )

        present = [
            c["type"]
            for c in bp["components"]
        ]

        for component_type in required:

            if component_type not in present:
                errors.append(
                    f"Missing required component: {component_type}"
                )

        return errors


if __name__ == "__main__":

    import json

    with open(
        "circuit_blueprints.json",
        "r",
        encoding="utf-8"
    ) as f:

        blueprints = json.load(f)

    validator = CircuitValidation()

    print("\nCIRCUIT VALIDATION REPORT\n")

    for bp in blueprints:

        result = validator.validate(bp)

        print("=" * 60)
        print(bp["question_id"])
        print("VALID :", result["valid"])

        if result["errors"]:
            for err in result["errors"]:
                print(" -", err)
        else:
            print(" ✓ Passed")

