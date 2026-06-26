"""
CollisionDetector — layout-level overlap and constraint validation.

Checks computed positions for common layout problems and emits warnings.
Never blocks rendering — all issues are reported via the logger only.
"""

import logging
from visualq_diagram_engine.layouts.layout_engine import Box

logger = logging.getLogger(__name__)


def _overlaps(a: Box, b: Box, tolerance: float = 2.0) -> bool:
    return (
        a.x < b.right  - tolerance and
        a.right  > b.x + tolerance and
        a.y < b.bottom - tolerance and
        a.bottom > b.y + tolerance
    )


class CollisionDetector:
    """
    Validates layout boxes computed by SemiconductorLayout / CircuitLayout.

    Usage::
        cd = CollisionDetector(canvas_w=900, canvas_h=480)
        cd.check_regions(semi_layout.as_regions())
        cd.check_carriers_in_region(carrier_box, region_box, "hole_grid", "p_region")
        cd.check_caption(caption_y, canvas_h=480)
    """

    def __init__(self, canvas_w: float = 900.0, canvas_h: float = 480.0):
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h

    # ── region checks ────────────────────────────────────────────────────────

    CONTAINER_REGIONS = {"semiconductor"}   # these legitimately contain sub-regions

    def check_regions(self, regions: dict[str, dict]) -> None:
        """Check that named regions are non-overlapping and inside canvas.

        Container regions (like 'semiconductor') that intentionally enclose
        sub-regions are excluded from the overlap check.
        """
        boxes = {name: Box.from_region(r, name) for name, r in regions.items()}

        for name, box in boxes.items():
            self._check_inside_canvas(box)

        names = [n for n in boxes if n not in self.CONTAINER_REGIONS]
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = boxes[names[i]], boxes[names[j]]
                if _overlaps(a, b):
                    logger.warning(
                        "Layout: regions '%s' and '%s' overlap", names[i], names[j]
                    )

    def check_carriers_in_region(
        self, carrier_box: Box, region_box: Box,
        carrier_id: str, region_name: str,
    ) -> None:
        """Warn if a carrier grid bounding box extends outside its region."""
        if (carrier_box.x < region_box.x - 1 or
                carrier_box.right > region_box.right + 1 or
                carrier_box.y < region_box.y - 1 or
                carrier_box.bottom > region_box.bottom + 1):
            logger.warning(
                "Layout: carrier grid '%s' extends outside region '%s'",
                carrier_id, region_name,
            )

    def check_caption(self, caption_y: float, bottom_margin: float = 20.0) -> None:
        """Warn if caption is outside the canvas."""
        if caption_y > self.canvas_h - bottom_margin:
            logger.warning(
                "Layout: caption at y=%.0f may be clipped (canvas_h=%.0f)",
                caption_y, self.canvas_h,
            )
        if caption_y < 0:
            logger.warning("Layout: caption y=%.0f is above canvas top", caption_y)

    def check_wire_connects(
        self,
        wire_end: tuple[float, float],
        port: tuple[float, float],
        wire_id: str,
        tolerance: float = 3.0,
    ) -> None:
        """Warn if a wire endpoint does not land on the expected port."""
        dx = abs(wire_end[0] - port[0])
        dy = abs(wire_end[1] - port[1])
        if dx > tolerance or dy > tolerance:
            logger.warning(
                "Layout: wire '%s' endpoint (%.0f,%.0f) does not match port (%.0f,%.0f)",
                wire_id, wire_end[0], wire_end[1], port[0], port[1],
            )

    def check_boxes(self, named_boxes: dict[str, Box]) -> None:
        """Generic overlap check for a set of named boxes."""
        names = list(named_boxes.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = named_boxes[names[i]], named_boxes[names[j]]
                if _overlaps(a, b):
                    logger.warning(
                        "Layout collision: '%s' and '%s' overlap", names[i], names[j]
                    )

    # ── private ──────────────────────────────────────────────────────────────

    def _check_inside_canvas(self, box: Box, tolerance: float = 1.0) -> None:
        if (box.x < -tolerance or box.right > self.canvas_w + tolerance or
                box.y < -tolerance or box.bottom > self.canvas_h + tolerance):
            logger.warning(
                "Layout: box '%s' extends outside canvas (%.0f×%.0f)",
                box.label, self.canvas_w, self.canvas_h,
            )
