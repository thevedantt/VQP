"""Scene builder — converts a parsed spec dict into a Scene graph."""

import logging
from typing import Any

from visualq_diagram_engine.core.scene import Scene, Layer, SceneNode
from visualq_diagram_engine.primitives.styles import Style
from visualq_diagram_engine.primitives.rectangle import Rectangle
from visualq_diagram_engine.primitives.circle import Circle
from visualq_diagram_engine.primitives.ellipse import Ellipse
from visualq_diagram_engine.primitives.line import Line
from visualq_diagram_engine.primitives.arrow import Arrow
from visualq_diagram_engine.primitives.polygon import Polygon
from visualq_diagram_engine.primitives.bezier import BezierPath
from visualq_diagram_engine.primitives.text import Text
from visualq_diagram_engine.primitives.group import Group
from visualq_diagram_engine.primitives.carrier_grid import CarrierGrid
from visualq_diagram_engine.primitives.battery_symbol import BatterySymbol
from visualq_diagram_engine.primitives.resistor_symbol import ResistorSymbol
from visualq_diagram_engine.primitives.switch_symbol import SwitchSymbol
from visualq_diagram_engine.primitives.ion_grid import IonGrid
from visualq_diagram_engine.primitives.field_arrow import FieldArrow
from visualq_diagram_engine.primitives.wire_path import WirePath

logger = logging.getLogger(__name__)


class SceneBuilder:
    def __init__(self) -> None:
        self._regions: dict[str, dict] = {}   # named regions from scene.regions
        self._scene_w: float = 800.0
        self._scene_h: float = 600.0

    def build(self, spec: dict) -> Scene:
        """Build a Scene from a validated spec dict."""
        scene_spec = spec["scene"]
        self._scene_w = float(scene_spec.get("width", 800))
        self._scene_h = float(scene_spec.get("height", 600))
        self._regions = {
            k: dict(v) for k, v in (scene_spec.get("regions") or {}).items()
        }

        scene = Scene(
            title=scene_spec.get("title", "Untitled"),
            width=self._scene_w,
            height=self._scene_h,
            background=scene_spec.get("background", "#FFFFFF"),
        )

        for layer_spec in spec.get("layers", []):
            layer = Layer(
                name=layer_spec.get("name", "layer"),
                z_index=int(layer_spec.get("z_index", 0)),
            )
            for obj_spec in layer_spec.get("objects", []):
                node = self._build_node(obj_spec)
                if node is not None:
                    layer.add(node)
            scene.add_layer(layer)

        total = sum(len(l.objects) for l in scene.layers)
        logger.debug("Scene built: %d layers, %d objects", len(scene.layers), total)
        return scene

    # ── Region resolution helpers ──────────────────────────────────────────

    def _region(self, name: str) -> dict | None:
        return self._regions.get(name)

    def _center_grid_in_region(
        self,
        region: dict,
        cols: int, rows: int,
        spacing_x: float, spacing_y: float,
        radius: float,
        margin: float,
    ) -> tuple[float, float]:
        """Return (origin_x, origin_y) of the top-left carrier centre,
        centred inside region with the given margin."""
        rx, ry = float(region["x"]), float(region["y"])
        rw, rh = float(region["width"]), float(region["height"])
        content_w = (cols - 1) * spacing_x
        content_h = (rows - 1) * spacing_y
        avail_w = rw - 2 * margin
        avail_h = rh - 2 * margin
        ox = rx + margin + max(0.0, (avail_w - content_w) / 2)
        oy = ry + margin + max(0.0, (avail_h - content_h) / 2)
        return (ox, oy)

    def _ion_position_from_region(
        self,
        region: dict,
        depletion_side: str,
        rows: int,
        spacing_y: float,
    ) -> tuple[float, float]:
        """Return (cx, top_y) for an ion column inside a depletion region."""
        rx, ry = float(region["x"]), float(region["y"])
        rw, rh = float(region["width"]), float(region["height"])
        cx = rx + rw / 4 if depletion_side == "left" else rx + rw * 3 / 4
        grid_h = (rows - 1) * spacing_y
        top_y = ry + (rh - grid_h) / 2
        return (cx, top_y)

    def _field_arrow_from_region(
        self,
        region: dict,
        direction: str,
        margin: float,
        y_align: str,
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        """Return (start, end) for a field arrow spanning a region."""
        rx, ry = float(region["x"]), float(region["y"])
        rw, rh = float(region["width"]), float(region["height"])
        y = ry + rh / 2 if y_align == "center" else ry + float(y_align)
        right_x = rx + rw
        if direction == "left":
            return ((right_x - margin, y), (rx + margin, y))
        elif direction == "right":
            return ((rx + margin, y), (right_x - margin, y))
        elif direction == "up":
            return ((rx + rw / 2, ry + rh - margin), (rx + rw / 2, ry + margin))
        else:  # down
            return ((rx + rw / 2, ry + margin), (rx + rw / 2, ry + rh - margin))

    def _parse_style(self, spec: dict) -> Style:
        style_dict = spec.get("style", {}) or {}
        valid_keys = set(Style.model_fields.keys())
        filtered = {k: v for k, v in style_dict.items() if k in valid_keys}
        return Style(**filtered)

    def _build_node(self, spec: dict) -> SceneNode | None:
        obj_type = spec.get("type", "").lower()
        node_id = spec.get("id", f"node_{id(spec)}")
        style = self._parse_style(spec)

        try:
            if obj_type == "rectangle":
                region_name = spec.get("region")
                if region_name:
                    rg = self._region(region_name)
                    if rg:
                        x, y = float(rg["x"]), float(rg["y"])
                        w, h = float(rg["width"]), float(rg["height"])
                    else:
                        logger.warning("rectangle '%s': region '%s' not found", node_id, region_name)
                        x, y, w, h = 0.0, 0.0, 0.0, 0.0
                else:
                    x = float(spec.get("x", 0))
                    y = float(spec.get("y", 0))
                    w = float(spec.get("width", 0))
                    h = float(spec.get("height", 0))
                return Rectangle(
                    id=node_id,
                    position=(x, y),
                    width=w,
                    height=h,
                    corner_radius=float(spec.get("corner_radius", 0)),
                    style=style,
                )

            elif obj_type == "circle":
                return Circle(
                    id=node_id,
                    position=(float(spec.get("x", 0)), float(spec.get("y", 0))),
                    radius=float(spec.get("radius", 0)),
                    style=style,
                )

            elif obj_type == "ellipse":
                return Ellipse(
                    id=node_id,
                    position=(float(spec.get("x", 0)), float(spec.get("y", 0))),
                    rx=float(spec.get("rx", 0)),
                    ry=float(spec.get("ry", 0)),
                    style=style,
                )

            elif obj_type == "line":
                # boundary: left/right on a region → dashed vertical boundary line
                boundary = spec.get("boundary")
                region_name = spec.get("region")
                if boundary and region_name:
                    rg = self._region(region_name)
                    if rg:
                        rx, ry = float(rg["x"]), float(rg["y"])
                        rh = float(rg["height"])
                        bx = rx if boundary == "left" else rx + float(rg["width"])
                        sx, sy, ex, ey = bx, ry, bx, ry + rh
                    else:
                        logger.warning("line '%s': region '%s' not found", node_id, region_name)
                        sx = sy = ex = ey = 0.0
                else:
                    sx = float(spec.get("start_x", 0))
                    sy = float(spec.get("start_y", 0))
                    ex = float(spec.get("end_x",   0))
                    ey = float(spec.get("end_y",   0))
                return Line(
                    id=node_id,
                    position=(sx, sy),
                    start=(sx, sy),
                    end=(ex, ey),
                    style=style,
                )

            elif obj_type == "arrow":
                return Arrow(
                    id=node_id,
                    position=(float(spec.get("start_x", 0)), float(spec.get("start_y", 0))),
                    start=(float(spec.get("start_x", 0)), float(spec.get("start_y", 0))),
                    end=(float(spec.get("end_x", 0)), float(spec.get("end_y", 0))),
                    head_size=float(spec.get("head_size", 10)),
                    bidirectional=bool(spec.get("bidirectional", False)),
                    style=style,
                )

            elif obj_type == "polygon":
                raw_points = spec.get("points", [])
                points = [(float(p[0]), float(p[1])) for p in raw_points]
                return Polygon(
                    id=node_id,
                    position=(float(spec.get("x", 0)), float(spec.get("y", 0))),
                    points=points,
                    style=style,
                )

            elif obj_type == "bezier":
                return BezierPath(
                    id=node_id,
                    position=(float(spec.get("x", 0)), float(spec.get("y", 0))),
                    path_data=spec.get("path_data", ""),
                    style=style,
                )

            elif obj_type == "text":
                # label_anchor: top_center / bottom_center / left_center / right_center
                # combined with region: and y_offset: for automatic label placement
                anchor = spec.get("label_anchor")
                region_name = spec.get("region")
                if anchor and region_name:
                    rg = self._region(region_name)
                    if rg:
                        rx, ry = float(rg["x"]), float(rg["y"])
                        rw, rh = float(rg["width"]), float(rg["height"])
                        off_y = float(spec.get("y_offset", 0))
                        off_x = float(spec.get("x_offset", 0))
                        tx = {
                            "top_center":    rx + rw / 2,
                            "bottom_center": rx + rw / 2,
                            "left_center":   rx,
                            "right_center":  rx + rw,
                            "center":        rx + rw / 2,
                        }.get(anchor, rx + rw / 2) + off_x
                        ty = {
                            "top_center":    ry + off_y,
                            "bottom_center": ry + rh + off_y,
                            "left_center":   ry + rh / 2 + off_y,
                            "right_center":  ry + rh / 2 + off_y,
                            "center":        ry + rh / 2 + off_y,
                        }.get(anchor, ry + off_y)
                    else:
                        logger.warning("text '%s': region '%s' not found", node_id, region_name)
                        tx = float(spec.get("x", 0))
                        ty = float(spec.get("y", 0))
                else:
                    tx = float(spec.get("x", 0))
                    ty = float(spec.get("y", 0))
                return Text(
                    id=node_id,
                    position=(tx, ty),
                    content=str(spec.get("content", "")),
                    style=style,
                )

            elif obj_type == "group":
                group = Group(
                    id=node_id,
                    position=(float(spec.get("x", 0)), float(spec.get("y", 0))),
                    style=style,
                )
                for child_spec in spec.get("children", []):
                    child = self._build_node(child_spec)
                    if child:
                        group.add(child)
                return group

            elif obj_type == "carrier_grid":
                rows   = int(spec.get("rows", 3))
                cols   = int(spec.get("cols", 3))
                sx     = float(spec.get("spacing_x", 55))
                sy     = float(spec.get("spacing_y", 50))
                radius = float(spec.get("carrier_radius", 8))
                margin = float(spec.get("margin", 20))
                align  = str(spec.get("align", ""))
                region_name = spec.get("region")

                if region_name and align == "center":
                    region = self._region(region_name)
                    if region:
                        pos = self._center_grid_in_region(
                            region, cols, rows, sx, sy, radius, margin
                        )
                    else:
                        logger.warning("carrier_grid '%s': region '%s' not found", node_id, region_name)
                        pos = (float(spec.get("x", 0)), float(spec.get("y", 0)))
                else:
                    pos = (float(spec.get("x", 0)), float(spec.get("y", 0)))

                return CarrierGrid(
                    id=node_id,
                    position=pos,
                    rows=rows,
                    cols=cols,
                    spacing_x=sx,
                    spacing_y=sy,
                    carrier_type=str(spec.get("carrier_type", "hole")),
                    carrier_radius=radius,
                    show_arrows=bool(spec.get("show_arrows", False)),
                    arrow_direction=str(spec.get("arrow_direction", "right")),
                    arrow_length=float(spec.get("arrow_length", 20)),
                    style=style,
                )

            elif obj_type == "ion_grid":
                rows      = int(spec.get("rows", 3))
                spacing_y = float(spec.get("spacing_y", 45))
                spacing_x = float(spec.get("spacing_x", 30))
                cols      = int(spec.get("cols", 1))
                region_name    = spec.get("region")
                depletion_side = spec.get("depletion_side")

                if region_name and depletion_side:
                    region = self._region(region_name)
                    if region:
                        pos = self._ion_position_from_region(
                            region, depletion_side, rows, spacing_y
                        )
                    else:
                        logger.warning("ion_grid '%s': region '%s' not found", node_id, region_name)
                        pos = (float(spec.get("x", 0)), float(spec.get("y", 0)))
                else:
                    pos = (float(spec.get("x", 0)), float(spec.get("y", 0)))

                fs = style.font_size if style.font_size else 14.0
                return IonGrid(
                    id=node_id,
                    position=pos,
                    rows=rows,
                    cols=cols,
                    spacing_x=spacing_x,
                    spacing_y=spacing_y,
                    charge=str(spec.get("charge", "positive")),
                    symbol_size=fs,
                    style=style,
                )

            elif obj_type == "field_arrow":
                region_name = spec.get("region")
                direction   = str(spec.get("direction", "right"))
                y_align     = str(spec.get("y_align", "center"))
                fa_margin   = float(spec.get("margin", 10))

                if region_name:
                    region = self._region(region_name)
                    if region:
                        start, end = self._field_arrow_from_region(
                            region, direction, fa_margin, y_align
                        )
                    else:
                        logger.warning("field_arrow '%s': region '%s' not found", node_id, region_name)
                        start = (float(spec.get("start_x", 0)), float(spec.get("start_y", 0)))
                        end   = (float(spec.get("end_x", 0)),   float(spec.get("end_y", 0)))
                else:
                    start = (float(spec.get("start_x", 0)), float(spec.get("start_y", 0)))
                    end   = (float(spec.get("end_x", 0)),   float(spec.get("end_y", 0)))

                return FieldArrow(
                    id=node_id,
                    position=start,
                    end=end,
                    head_size=float(spec.get("head_size", 7)),
                    label=str(spec.get("label", "")),
                    label_side=str(spec.get("label_side", "above")),
                    label_offset=float(spec.get("label_offset", 12)),
                    style=style,
                )

            elif obj_type == "wire_path":
                raw = spec.get("waypoints", [])
                waypoints = [(float(p[0]), float(p[1])) for p in raw]
                return WirePath(
                    id=node_id,
                    position=(0.0, 0.0),
                    waypoints=waypoints,
                    style=style,
                )

            elif obj_type == "battery_symbol":
                return BatterySymbol(
                    id=node_id,
                    position=(float(spec.get("x", 0)), float(spec.get("y", 0))),
                    orientation=str(spec.get("orientation", "horizontal")),
                    positive_on=str(spec.get("positive_on", "left")),
                    cells=int(spec.get("cells", 1)),
                    style=style,
                )

            elif obj_type == "resistor_symbol":
                return ResistorSymbol(
                    id=node_id,
                    position=(float(spec.get("x", 0)), float(spec.get("y", 0))),
                    length=float(spec.get("length", 70)),
                    body_height=float(spec.get("body_height", 14)),
                    orientation=str(spec.get("orientation", "horizontal")),
                    label=str(spec.get("label", "R")),
                    style=style,
                )

            elif obj_type == "switch_symbol":
                return SwitchSymbol(
                    id=node_id,
                    position=(float(spec.get("x", 0)), float(spec.get("y", 0))),
                    length=float(spec.get("length", 45)),
                    open=bool(spec.get("open", False)),
                    orientation=str(spec.get("orientation", "horizontal")),
                    label=str(spec.get("label", "K")),
                    style=style,
                )

            else:
                logger.warning("Unknown object type '%s' (id=%s), skipping", obj_type, node_id)
                return None

        except Exception as exc:
            logger.error("Failed to build node '%s' (type=%s): %s", node_id, obj_type, exc)
            return None
