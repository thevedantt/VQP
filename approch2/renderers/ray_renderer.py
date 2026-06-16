from physics_solver import PhysicsSolver
from ray_math import RayMath
from ray_rules import RULES

_ARROWHEAD_SIZE = 8
_CANVAS_W = 1200
_CANVAS_H = 700
_AXIS_Y = 300
_LENS_X = 500
_FOCAL_LENGTH = 100.0
_LENS_HALF_HEIGHT = 160
_MARGIN = 40


class RayRenderer:

    def __init__(self):
        self.solver = PhysicsSolver(focal_length=_FOCAL_LENGTH)
        self.ray_math = RayMath(focal_length=_FOCAL_LENGTH)

    # ------------------------------------------------------------------ #
    #  SVG scaffolding
    # ------------------------------------------------------------------ #

    def _svg_header(self) -> str:
        ah = _ARROWHEAD_SIZE
        half = ah / 2.0
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{_CANVAS_W}" height="{_CANVAS_H}">
<defs>
  <marker id="ah" markerWidth="{ah}" markerHeight="{ah}" refX="{ah}" refY="{half}" orient="auto">
    <polygon points="0,0 {ah},{half} 0,{ah}" fill="black"/>
  </marker>
  <marker id="ah-red" markerWidth="{ah}" markerHeight="{ah}" refX="{ah}" refY="{half}" orient="auto">
    <polygon points="0,0 {ah},{half} 0,{ah}" fill="#cc0000"/>
  </marker>
  <marker id="ah-green" markerWidth="{ah}" markerHeight="{ah}" refX="{ah}" refY="{half}" orient="auto">
    <polygon points="0,0 {ah},{half} 0,{ah}" fill="#006600"/>
  </marker>
  <marker id="ah-blue" markerWidth="{ah}" markerHeight="{ah}" refX="{ah}" refY="{half}" orient="auto">
    <polygon points="0,0 {ah},{half} 0,{ah}" fill="#0000cc"/>
  </marker>
</defs>
"""

    @staticmethod
    def _svg_footer() -> str:
        return "</svg>"

    # ------------------------------------------------------------------ #
    #  Static elements
    # ------------------------------------------------------------------ #

    def _principal_axis(self) -> str:
        return f"""
<line x1="{_MARGIN}" y1="{_AXIS_Y}" x2="{_CANVAS_W - _MARGIN}" y2="{_AXIS_Y}" stroke="#333" stroke-width="1.5" marker-end="url(#ah)"/>"""

    def _lens(self) -> str:
        cx = _LENS_X
        cy = _AXIS_Y
        rx = 15
        ry = _LENS_HALF_HEIGHT
        return f"""
<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="#1a1aff" stroke-width="3"/>
<line x1="{cx}" y1="{cy - ry}" x2="{cx}" y2="{cy + ry}" stroke="#1a1aff" stroke-width="1.5" stroke-dasharray="4,4"/>"""

    def _focal_labels(self, f1: float, f2: float, two_f1: float, two_f2: float) -> str:
        y = _AXIS_Y
        return f"""
<circle cx="{f1}" cy="{y}" r="3.5" fill="#333"/>
<circle cx="{f2}" cy="{y}" r="3.5" fill="#333"/>
<circle cx="{two_f1}" cy="{y}" r="3.5" fill="#333"/>
<circle cx="{two_f2}" cy="{y}" r="3.5" fill="#333"/>
<line x1="{two_f1}" y1="{y - 6}" x2="{two_f1}" y2="{y + 6}" stroke="#333" stroke-width="1"/>
<line x1="{f1}" y1="{y - 6}" x2="{f1}" y2="{y + 6}" stroke="#333" stroke-width="1"/>
<line x1="{_LENS_X}" y1="{y - 6}" x2="{_LENS_X}" y2="{y + 6}" stroke="#333" stroke-width="1"/>
<line x1="{f2}" y1="{y - 6}" x2="{f2}" y2="{y + 6}" stroke="#333" stroke-width="1"/>
<line x1="{two_f2}" y1="{y - 6}" x2="{two_f2}" y2="{y + 6}" stroke="#333" stroke-width="1"/>
<text x="{two_f1}" y="{y + 28}" text-anchor="middle" font-size="15" font-family="Arial, sans-serif" font-weight="bold">2F\u2081</text>
<text x="{f1}" y="{y + 28}" text-anchor="middle" font-size="15" font-family="Arial, sans-serif" font-weight="bold">F\u2081</text>
<text x="{_LENS_X}" y="{y + 28}" text-anchor="middle" font-size="15" font-family="Arial, sans-serif" font-weight="bold">O</text>
<text x="{f2}" y="{y + 28}" text-anchor="middle" font-size="15" font-family="Arial, sans-serif" font-weight="bold">F\u2082</text>
<text x="{two_f2}" y="{y + 28}" text-anchor="middle" font-size="15" font-family="Arial, sans-serif" font-weight="bold">2F\u2082</text>"""

    # ------------------------------------------------------------------ #
    #  Line helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _line_seg(x1: float, y1: float, x2: float, y2: float, color: str, width: int = 2, dash: str = "", marker: str = "") -> str:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        marker_attr = f' marker-end="url(#{marker})"' if marker else ""
        return f"""
<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{dash_attr}{marker_attr}/>"""

    @staticmethod
    def _arrowhead_point(x1: float, y1: float, x2: float, y2: float) -> tuple[float, float]:
        dx = x2 - x1
        dy = y2 - y1
        length = (dx * dx + dy * dy) ** 0.5
        if length < 1:
            return x2, y2
        fraction = 1.0 - _ARROWHEAD_SIZE / length
        return x1 + dx * fraction, y1 + dy * fraction

    def _line_with_arrow(self, x1: float, y1: float, x2: float, y2: float, color: str, marker: str, dash: str = "") -> str:
        ax, ay = self._arrowhead_point(x1, y1, x2, y2)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        return f"""
<line x1="{x1}" y1="{y1}" x2="{ax}" y2="{ay}" stroke="{color}" stroke-width="2"{dash_attr} marker-end="url(#{marker})"/>
<line x1="{ax}" y1="{ay}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"{dash_attr}/>"""

    # ------------------------------------------------------------------ #
    #  Object & image arrows
    # ------------------------------------------------------------------ #

    def _object_arrow(self, obj_x: float, obj_top_y: float) -> str:
        return f"""
<line x1="{obj_x}" y1="{_AXIS_Y}" x2="{obj_x}" y2="{obj_top_y}" stroke="black" stroke-width="3" marker-end="url(#ah)"/>
<text x="{obj_x - 10}" y="{obj_top_y - 12}" text-anchor="end" font-size="15" font-family="Arial, sans-serif" font-style="italic">Object</text>"""

    def _image_arrow(self, img_x: float, img_top_y: float, is_virtual: bool) -> str:
        dash = ' stroke-dasharray="7,5"' if is_virtual else ""
        label = "Virtual Image" if is_virtual else "Image"
        label_y = img_top_y - 12 if img_top_y < _AXIS_Y else img_top_y + 28
        return f"""
<line x1="{img_x}" y1="{_AXIS_Y}" x2="{img_x}" y2="{img_top_y}" stroke="black" stroke-width="3"{dash} marker-end="url(#ah)"/>
<text x="{img_x + 10}" y="{label_y}" text-anchor="start" font-size="15" font-family="Arial, sans-serif" font-style="italic">{label}</text>"""

    # ------------------------------------------------------------------ #
    #  Ray 1 — parallel to axis, refracts through F2
    # ------------------------------------------------------------------ #

    def _build_parallel_ray(
        self, obj_x: float, obj_top_y: float, lens_x: float, f2: float,
        image_x: float, image_top_y: float, ray_mode: str
    ) -> str:
        hit_y = obj_top_y

        before = self._line_seg(obj_x, obj_top_y, lens_x, hit_y, "#cc0000")

        if ray_mode == "real":
            return before + self._line_with_arrow(lens_x, hit_y, image_x, image_top_y, "#cc0000", "ah-red")

        slope = (hit_y - _AXIS_Y) / (lens_x - f2) if abs(lens_x - f2) > 0.01 else 0
        forward_end_x = min(lens_x + 350, _CANVAS_W - _MARGIN)
        forward_end_y = _AXIS_Y + slope * (forward_end_x - f2)
        forward_end_y = max(-_CANVAS_H, min(_CANVAS_H * 2, forward_end_y))

        after_solid = self._line_with_arrow(lens_x, hit_y, forward_end_x, forward_end_y, "#cc0000", "ah-red")
        back_ext = self._line_seg(lens_x, hit_y, image_x, image_top_y, "#cc0000", width=1, dash="7,5")

        return before + after_solid + back_ext

    # ------------------------------------------------------------------ #
    #  Ray 2 — through optical centre, undeviated
    # ------------------------------------------------------------------ #

    def _build_oc_ray(
        self, obj_x: float, obj_top_y: float, lens_x: float,
        image_x: float, image_top_y: float, ray_mode: str
    ) -> str:
        if ray_mode == "real":
            return self._line_with_arrow(obj_x, obj_top_y, image_x, image_top_y, "#006600", "ah-green")

        slope = (obj_top_y - _AXIS_Y) / (obj_x - lens_x) if abs(obj_x - lens_x) > 0.01 else 0
        forward_end_x = min(lens_x + 350, _CANVAS_W - _MARGIN)
        forward_end_y = _AXIS_Y + slope * (forward_end_x - lens_x)
        forward_end_y = max(-_CANVAS_H, min(_CANVAS_H * 2, forward_end_y))

        obj_to_o = self._line_seg(obj_x, obj_top_y, lens_x, _AXIS_Y, "#006600")
        o_to_forward = self._line_with_arrow(lens_x, _AXIS_Y, forward_end_x, forward_end_y, "#006600", "ah-green")
        back_ext = self._line_seg(lens_x, _AXIS_Y, image_x, image_top_y, "#006600", width=1, dash="7,5")

        return obj_to_o + o_to_forward + back_ext

    # ------------------------------------------------------------------ #
    #  Ray 3 — through F1, emerges parallel to axis
    #  Only drawn for real-image cases (object left of F1).
    # ------------------------------------------------------------------ #

    def _build_focal_ray(
        self, obj_x: float, obj_top_y: float, lens_x: float, f1: float,
        image_x: float, image_top_y: float, ray_mode: str
    ) -> str:
        if ray_mode == "virtual":
            return ""
        if obj_x >= f1:
            return ""

        t = (lens_x - obj_x) / (f1 - obj_x)
        lens_hit_y = obj_top_y + t * (_AXIS_Y - obj_top_y)

        incident = self._line_with_arrow(obj_x, obj_top_y, lens_x, lens_hit_y, "#0000cc", "ah-blue")

        exit_end_x = image_x if image_x > lens_x else _CANVAS_W - _MARGIN
        exit_end_y = lens_hit_y

        emergent = self._line_with_arrow(lens_x, lens_hit_y, exit_end_x, exit_end_y, "#0000cc", "ah-blue")

        return incident + emergent

    # ------------------------------------------------------------------ #
    #  Vertical guide line at image position
    # ------------------------------------------------------------------ #

    def _image_guide(self, image_x: float, image_height: float) -> str:
        y1 = _AXIS_Y - image_height - 30
        y2 = _AXIS_Y + max(image_height, 20) + 10
        return f"""
<line x1="{image_x}" y1="{y1}" x2="{image_x}" y2="{y2}"
      stroke="#999" stroke-width="1" stroke-dasharray="3,3"/>"""

    # ------------------------------------------------------------------ #
    #  Main entry point
    # ------------------------------------------------------------------ #

    def render_convex_lens(self, blueprint: dict) -> str:
        scenario = blueprint.get("scenario", "between_f_and_2f")
        lens_x = blueprint.get("lens", {}).get("x", _LENS_X)
        axis_y = blueprint.get("principal_axis", {}).get("y", _AXIS_Y)

        object_x = blueprint.get("object", {}).get("x", 350)
        object_height = blueprint.get("object", {}).get("height", 100)
        obj_top_y = axis_y - object_height

        fp = self.ray_math.focal_points(lens_x)
        f1, f2, two_f1, two_f2 = fp["F1"], fp["F2"], fp["2F1"], fp["2F2"]

        result = self.solver.solve_convex_lens(lens_x, object_x, object_height, scenario)
        image_x = result["image_x"]
        image_height = result["image_height"]
        orientation = result["orientation"]
        is_virtual = result["image_type"] == "virtual"
        ray_mode = "virtual" if is_virtual else "real"

        if orientation == "inverted":
            image_top_y = axis_y + image_height
        else:
            image_top_y = axis_y - image_height

        svg = self._svg_header()
        svg += self._principal_axis()
        svg += self._lens()
        svg += self._focal_labels(f1, f2, two_f1, two_f2)
        svg += self._image_guide(image_x, image_height)

        svg += f"""
<!-- Rays -->{self._build_parallel_ray(object_x, obj_top_y, lens_x, f2, image_x, image_top_y, ray_mode)}
{self._build_oc_ray(object_x, obj_top_y, lens_x, image_x, image_top_y, ray_mode)}
{self._build_focal_ray(object_x, obj_top_y, lens_x, f1, image_x, image_top_y, ray_mode)}"""

        svg += self._object_arrow(object_x, obj_top_y)
        svg += self._image_arrow(image_x, image_top_y, is_virtual)

        if is_virtual:
            label_y = axis_y + image_height + 28
            svg += f"""
<text x="{image_x}" y="{label_y}" text-anchor="middle" font-size="13" font-family="Arial, sans-serif" fill="#666" font-style="italic">(virtual)</text>"""

        scenario_label = scenario.replace("_", " ").title()
        svg += f"""
<text x="{_CANVAS_W / 2}" y="35" text-anchor="middle" font-size="18" font-family="Arial, sans-serif" font-weight="bold">Ray Diagram — Convex Lens</text>
<text x="{_CANVAS_W / 2}" y="55" text-anchor="middle" font-size="14" font-family="Arial, sans-serif" fill="#555">Object {scenario_label}</text>
"""

        svg += self._svg_footer()
        return svg
