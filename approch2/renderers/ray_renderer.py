from physics_solver import PhysicsSolver
from ray_math import RayMath
from ray_rules import RULES

_ARROW_SIZE = 10
_CANVAS_W = 1200
_CANVAS_H = 700
_AXIS_Y = 300
_LENS_X = 500
_FOCAL_LENGTH = 100.0
_LENS_HALF_H = 160
_LENS_BULGE = 22
_MARGIN = 40


class RayRenderer:

    def __init__(self):
        self.solver = PhysicsSolver(focal_length=_FOCAL_LENGTH)
        self.ray_math = RayMath(focal_length=_FOCAL_LENGTH)

    # ------------------------------------------------------------------ #
    #  SVG scaffolding
    # ------------------------------------------------------------------ #

    def _svg_header(self) -> str:
        a = _ARROW_SIZE
        h = a / 2.0
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{_CANVAS_W}" height="{_CANVAS_H}">
<defs>
  <marker id="ah" markerWidth="{a}" markerHeight="{a}" refX="{a}" refY="{h}" orient="auto">
    <polygon points="0,0 {a},{h} 0,{a}" fill="#222"/>
  </marker>
  <marker id="ah-rev" markerWidth="{a}" markerHeight="{a}" refX="0" refY="{h}" orient="auto">
    <polygon points="{a},0 0,{h} {a},{a}" fill="#222"/>
  </marker>
  <marker id="ah-red" markerWidth="{a}" markerHeight="{a}" refX="{a}" refY="{h}" orient="auto">
    <polygon points="0,0 {a},{h} 0,{a}" fill="#cc0000"/>
  </marker>
  <marker id="ah-green" markerWidth="{a}" markerHeight="{a}" refX="{a}" refY="{h}" orient="auto">
    <polygon points="0,0 {a},{h} 0,{a}" fill="#006600"/>
  </marker>
  <marker id="ah-blue" markerWidth="{a}" markerHeight="{a}" refX="{a}" refY="{h}" orient="auto">
    <polygon points="0,0 {a},{h} 0,{a}" fill="#0000cc"/>
  </marker>
</defs>
"""

    @staticmethod
    def _svg_footer() -> str:
        return "</svg>"

    # ------------------------------------------------------------------ #
    #  Static diagram elements
    # ------------------------------------------------------------------ #

    def _principal_axis(self) -> str:
        return f"""
<line x1="{_MARGIN}" y1="{_AXIS_Y}" x2="{_CANVAS_W - _MARGIN}" y2="{_AXIS_Y}" stroke="#222" stroke-width="2" marker-start="url(#ah-rev)" marker-end="url(#ah)"/>"""

    def _lens(self) -> str:
        cx = _LENS_X
        cy = _AXIS_Y
        ry = _LENS_HALF_H
        rx = _LENS_BULGE
        return f"""
<path d="M {cx},{cy - ry} Q {cx + rx},{cy} {cx},{cy + ry} Q {cx - rx},{cy} {cx},{cy - ry}" fill="none" stroke="#1a1aff" stroke-width="2.5" stroke-linejoin="round"/>
<line x1="{cx}" y1="{cy - ry}" x2="{cx}" y2="{cy + ry}" stroke="#1a1aff" stroke-width="1.5" stroke-dasharray="5,4"/>
<circle cx="{cx}" cy="{cy}" r="2.5" fill="#1a1aff"/>"""

    def _focal_markers(self, f1: float, f2: float, two_f1: float, two_f2: float) -> str:
        y = _AXIS_Y
        pts = [(two_f1, "2F\u2081"), (f1, "F\u2081"), (_LENS_X, "O"), (f2, "F\u2082"), (two_f2, "2F\u2082")]
        out = ""
        for px, _ in pts:
            out += f"""
<line x1="{px}" y1="{y - 7}" x2="{px}" y2="{y + 7}" stroke="#222" stroke-width="1.2"/>
<circle cx="{px}" cy="{y}" r="2.5" fill="#222"/>"""
        for px, label in pts:
            out += f"""
<text x="{px}" y="{y + 26}" text-anchor="middle" font-size="15" font-family="Arial, sans-serif" font-weight="bold">{label}</text>"""
        return out

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
    def _arrow_point(x1: float, y1: float, x2: float, y2: float) -> tuple[float, float]:
        dx = x2 - x1
        dy = y2 - y1
        length = (dx * dx + dy * dy) ** 0.5
        if length < 1:
            return x2, y2
        frac = 1.0 - _ARROW_SIZE / length
        return x1 + dx * frac, y1 + dy * frac

    def _line_arrow(self, x1: float, y1: float, x2: float, y2: float, color: str, marker: str, dash: str = "") -> str:
        ax, ay = self._arrow_point(x1, y1, x2, y2)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        return f"""
<line x1="{x1}" y1="{y1}" x2="{ax}" y2="{ay}" stroke="{color}" stroke-width="2"{dash_attr} marker-end="url(#{marker})"/>
<line x1="{ax}" y1="{ay}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"{dash_attr}/>"""

    # ------------------------------------------------------------------ #
    #  Object / image arrows
    # ------------------------------------------------------------------ #

    def _object_arrow(self, obj_x: float, obj_top_y: float) -> str:
        return f"""
<line x1="{obj_x}" y1="{_AXIS_Y}" x2="{obj_x}" y2="{obj_top_y}" stroke="#222" stroke-width="3" marker-end="url(#ah)"/>
<text x="{obj_x - 10}" y="{obj_top_y - 12}" text-anchor="end" font-size="15" font-family="Arial, sans-serif" font-style="italic">Object</text>"""

    def _image_arrow(self, img_x: float, img_top_y: float, is_virtual: bool) -> str:
        dash = ' stroke-dasharray="7,5"' if is_virtual else ""
        label = "Virtual Image" if is_virtual else "Image"
        label_y = img_top_y - 12 if img_top_y < _AXIS_Y else img_top_y + 28
        return f"""
<line x1="{img_x}" y1="{_AXIS_Y}" x2="{img_x}" y2="{img_top_y}" stroke="#222" stroke-width="3"{dash} marker-end="url(#ah)"/>
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
            return before + self._line_arrow(lens_x, hit_y, image_x, image_top_y, "#cc0000", "ah-red")

        slope = (hit_y - _AXIS_Y) / (lens_x - f2) if abs(lens_x - f2) > 0.01 else 0
        fx = min(lens_x + 350, _CANVAS_W - _MARGIN)
        fy = _AXIS_Y + slope * (fx - f2)
        fy = max(-_CANVAS_H, min(_CANVAS_H * 2, fy))

        solid = self._line_arrow(lens_x, hit_y, fx, fy, "#cc0000", "ah-red")
        back = self._line_seg(lens_x, hit_y, image_x, image_top_y, "#cc0000", width=1, dash="7,5")
        return before + solid + back

    # ------------------------------------------------------------------ #
    #  Ray 2 — through optical centre, undeviated
    # ------------------------------------------------------------------ #

    def _build_oc_ray(
        self, obj_x: float, obj_top_y: float, lens_x: float,
        image_x: float, image_top_y: float, ray_mode: str
    ) -> str:
        if ray_mode == "real":
            return self._line_arrow(obj_x, obj_top_y, image_x, image_top_y, "#006600", "ah-green")

        slope = (obj_top_y - _AXIS_Y) / (obj_x - lens_x) if abs(obj_x - lens_x) > 0.01 else 0
        fx = min(lens_x + 350, _CANVAS_W - _MARGIN)
        fy = _AXIS_Y + slope * (fx - lens_x)
        fy = max(-_CANVAS_H, min(_CANVAS_H * 2, fy))

        to_o = self._line_seg(obj_x, obj_top_y, lens_x, _AXIS_Y, "#006600")
        past_o = self._line_arrow(lens_x, _AXIS_Y, fx, fy, "#006600", "ah-green")
        back = self._line_seg(lens_x, _AXIS_Y, image_x, image_top_y, "#006600", width=1, dash="7,5")
        return to_o + past_o + back

    # ------------------------------------------------------------------ #
    #  Ray 3 — through F1, emerges parallel
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
        lhy = obj_top_y + t * (_AXIS_Y - obj_top_y)

        inc = self._line_arrow(obj_x, obj_top_y, lens_x, lhy, "#0000cc", "ah-blue")

        ex = image_x if image_x > lens_x else _CANVAS_W - _MARGIN
        ey = lhy
        emg = self._line_arrow(lens_x, lhy, ex, ey, "#0000cc", "ah-blue")
        return inc + emg

    # ------------------------------------------------------------------ #
    #  Guide line & intersection dot
    # ------------------------------------------------------------------ #

    def _image_guide(self, image_x: float, image_height: float) -> str:
        y1 = _AXIS_Y - image_height - 30
        y2 = _AXIS_Y + max(image_height, 20) + 10
        return f"""
<line x1="{image_x}" y1="{y1}" x2="{image_x}" y2="{y2}" stroke="#bbb" stroke-width="1" stroke-dasharray="4,4"/>"""

    def _intersection_dot(self, x: float, y: float) -> str:
        return f"""
<circle cx="{x}" cy="{y}" r="3" fill="#333"/>"""

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
        f1, f2 = fp["F1"], fp["F2"]

        result = self.solver.solve_convex_lens(lens_x, object_x, object_height, scenario)
        image_x = result["image_x"]
        image_height = result["image_height"]
        orientation = result["orientation"]
        is_virtual = result["image_type"] == "virtual"
        ray_mode = "virtual" if is_virtual else "real"

        image_top_y = axis_y + image_height if orientation == "inverted" else axis_y - image_height

        svg = self._svg_header()
        svg += self._principal_axis()
        svg += self._lens()
        svg += self._focal_markers(f1, f2, fp["2F1"], fp["2F2"])
        svg += self._image_guide(image_x, image_height)

        svg += f"""
<!-- Rays -->{self._build_parallel_ray(object_x, obj_top_y, lens_x, f2, image_x, image_top_y, ray_mode)}
{self._build_oc_ray(object_x, obj_top_y, lens_x, image_x, image_top_y, ray_mode)}
{self._build_focal_ray(object_x, obj_top_y, lens_x, f1, image_x, image_top_y, ray_mode)}"""

        if not is_virtual:
            svg += self._intersection_dot(image_x, image_top_y)

        svg += self._object_arrow(object_x, obj_top_y)
        svg += self._image_arrow(image_x, image_top_y, is_virtual)

        if is_virtual:
            ly = axis_y + image_height + 28
            svg += f"""
<text x="{image_x}" y="{ly}" text-anchor="middle" font-size="13" font-family="Arial, sans-serif" fill="#888" font-style="italic">(virtual)</text>"""

        scenario_label = scenario.replace("_", " ").title()
        svg += f"""
<text x="{_CANVAS_W / 2}" y="35" text-anchor="middle" font-size="18" font-family="Arial, sans-serif" font-weight="bold">Ray Diagram \u2014 Convex Lens</text>
<text x="{_CANVAS_W / 2}" y="55" text-anchor="middle" font-size="14" font-family="Arial, sans-serif" fill="#666">Object {scenario_label}</text>
"""
        svg += self._svg_footer()
        return svg
