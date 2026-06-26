"""Diagram spec and coordinate validator."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

REQUIRED_TOP_KEYS = {"scene", "layers"}

VALID_STYLE_KEYS = {
    "fill", "stroke", "stroke_width", "opacity",
    "font_size", "font_family", "font_weight",
    "text_anchor", "dash_array",
}

KNOWN_OBJECT_TYPES = {
    "rectangle", "circle", "ellipse", "line", "arrow",
    "polygon", "bezier", "text", "group",
    "carrier_grid", "ion_grid", "field_arrow", "wire_path",
    "battery_symbol", "resistor_symbol", "switch_symbol",
}

REQUIRED_REGION_KEYS = {"x", "y", "width", "height"}


class ValidationError(Exception):
    pass


class DiagramValidator:
    """Validates diagram specs before the scene builder processes them."""

    def validate_spec(self, spec: dict) -> None:
        """Raise ValidationError if required top-level structure is missing."""
        missing = REQUIRED_TOP_KEYS - set(spec.keys())
        if missing:
            raise ValidationError(
                f"Diagram spec missing required keys: {sorted(missing)}"
            )
        scene = spec["scene"]
        for key in ("width", "height"):
            if key not in scene:
                raise ValidationError(f"scene.{key} is required")
        if not isinstance(spec.get("layers", []), list):
            raise ValidationError("'layers' must be a list")

        # Validate named regions if present
        for name, region in (scene.get("regions") or {}).items():
            self._validate_region(name, region)

        # Validate each layer's objects
        for layer in spec.get("layers", []):
            for obj in layer.get("objects", []):
                self._validate_object(obj, scene)

    def _validate_region(self, name: str, region: dict) -> None:
        missing = REQUIRED_REGION_KEYS - set(region.keys())
        if missing:
            logger.warning(
                "Region '%s' is missing keys %s — auto-layout may fail", name, missing
            )

    def _validate_object(self, spec: dict, scene: dict) -> None:
        obj_type = spec.get("type", "")
        if obj_type and obj_type not in KNOWN_OBJECT_TYPES:
            logger.warning("Unknown object type '%s' — will be skipped", obj_type)

        obj_id = spec.get("id", "<unnamed>")

        # Carrier grid checks
        if obj_type == "carrier_grid":
            rows = spec.get("rows", 0)
            cols = spec.get("cols", 0)
            if not (1 <= rows <= 20 and 1 <= cols <= 20):
                logger.warning(
                    "carrier_grid '%s': rows=%s cols=%s seems unusual", obj_id, rows, cols
                )

        # Ion grid checks
        if obj_type == "ion_grid":
            charge = spec.get("charge", "")
            if charge not in ("positive", "negative", ""):
                logger.warning(
                    "ion_grid '%s': charge='%s' should be 'positive' or 'negative'",
                    obj_id, charge,
                )

        # Wire path checks
        if obj_type == "wire_path":
            wps = spec.get("waypoints", [])
            if len(wps) < 2:
                logger.warning("wire_path '%s' has fewer than 2 waypoints", obj_id)

        # Region reference check
        if "region" in spec:
            regions = (scene.get("regions") or {})
            if spec["region"] not in regions:
                logger.warning(
                    "Object '%s' references unknown region '%s'", obj_id, spec["region"]
                )

        # Coordinate bounds check (only for explicit x/y specs)
        if "x" in spec and "y" in spec:
            w = float(scene.get("width", 0))
            h = float(scene.get("height", 0))
            self.validate_coordinates(float(spec["x"]), float(spec["y"]), w, h)

    def validate_coordinates(
        self, x: float, y: float, max_w: float, max_h: float
    ) -> None:
        if max_w > 0 and max_h > 0:
            if x < 0 or x > max_w or y < 0 or y > max_h:
                logger.warning(
                    "Coordinate (%.0f, %.0f) is outside canvas (%.0f×%.0f)",
                    x, y, max_w, max_h,
                )

    def validate_style(self, style_dict: dict) -> None:
        unknown = set(style_dict.keys()) - VALID_STYLE_KEYS
        if unknown:
            logger.warning("Unknown style keys (ignored): %s", sorted(unknown))
