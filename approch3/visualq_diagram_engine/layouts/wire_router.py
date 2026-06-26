"""WireRouter — orthogonal wire routing between named connection ports."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Port:
    """
    A named connection point on a circuit component.

    direction indicates which way a wire exits this port:
    "right" means the wire continues to the right from (x, y).
    """
    name: str
    x: float
    y: float
    direction: str = "right"    # "left" | "right" | "up" | "down"


@dataclass
class WireSegment:
    """A single horizontal or vertical wire segment."""
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def is_horizontal(self) -> bool:
        return abs(self.y2 - self.y1) < 1e-6

    @property
    def is_vertical(self) -> bool:
        return abs(self.x2 - self.x1) < 1e-6

    def to_waypoints(self) -> list[tuple[float, float]]:
        return [(self.x1, self.y1), (self.x2, self.y2)]


class WireRouter:
    """
    Routes orthogonal wires between connection ports.

    Supports 0-turn (direct), 1-turn (L-shape), and 2-turn (Z/U-shape) routing.
    All output segments are axis-aligned.  No diagonal lines are produced.

    Usage example::

        router = WireRouter()
        p_contact = Port("p_left", x=130, y=230, direction="left")
        battery_entry = Port("battery_in", x=370, y=475, direction="left")
        segs = router.route(p_contact, battery_entry, via_y=475)
    """

    def route(
        self,
        from_port: Port,
        to_port: Port,
        via_y: Optional[float] = None,
        via_x: Optional[float] = None,
    ) -> list[WireSegment]:
        """
        Route from from_port to to_port.

        via_y: force an intermediate row (e.g. bottom of circuit loop).
        via_x: force an intermediate column.
        If neither is given, defaults to an L-shape (horizontal first).
        """
        fx, fy = from_port.x, from_port.y
        tx, ty = to_port.x, to_port.y

        if abs(fy - ty) < 1e-6:            # same row — direct horizontal
            return [WireSegment(fx, fy, tx, ty)]

        if abs(fx - tx) < 1e-6:            # same column — direct vertical
            return [WireSegment(fx, fy, fx, ty)]

        if via_y is not None:               # U/Z via a horizontal detour
            return [
                WireSegment(fx, fy, fx, via_y),
                WireSegment(fx, via_y, tx, via_y),
                WireSegment(tx, via_y, tx, ty),
            ]

        if via_x is not None:               # U/Z via a vertical detour
            return [
                WireSegment(fx, fy, via_x, fy),
                WireSegment(via_x, fy, via_x, ty),
                WireSegment(via_x, ty, tx, ty),
            ]

        # Default: L-shape, horizontal then vertical
        return [
            WireSegment(fx, fy, tx, fy),
            WireSegment(tx, fy, tx, ty),
        ]

    def merge_waypoints(self, segments: list[WireSegment]) -> list[tuple[float, float]]:
        """Collapse a list of segments into an ordered list of waypoints."""
        if not segments:
            return []
        pts: list[tuple[float, float]] = [(segments[0].x1, segments[0].y1)]
        for seg in segments:
            pts.append((seg.x2, seg.y2))
        return pts
