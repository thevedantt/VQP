import json
import math
from pathlib import Path

from fbd_layout import generate_layout


BLUEPRINT_FILE = Path(__file__).parent / "fbd_blueprints.json"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SVG_W = 800
SVG_H = 600
CX = 400
CY = 300


_INCLINE_START = (200, 420)
_INCLINE_END = (600, 200)
_IDX = _INCLINE_END[0] - _INCLINE_START[0]
_IDY = _INCLINE_END[1] - _INCLINE_START[1]
_INCLINE_ANGLE = math.degrees(math.atan2(_IDY, _IDX))
_INCLINE_LEN = math.hypot(_IDX, _IDY)
_UX = _IDX / _INCLINE_LEN
_UY = _IDY / _INCLINE_LEN
_NX = -_UY
_NY = _UX


def _svg_start():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}">
<defs>
  <marker id="ah" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
    <polygon points="0,0 10,3.5 0,7" fill="#222"/>
  </marker>
  <marker id="ah-gray" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
    <polygon points="0,0 10,3.5 0,7" fill="#999"/>
  </marker>
  <marker id="ah-open" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
    <polygon points="0,0 10,3.5 0,7" fill="#aaa"/>
  </marker>
</defs>
'''


def _svg_end():
    return '</svg>'


def _line(x1, y1, x2, y2, **kw):
    stroke = kw.get("stroke", "#222")
    width = kw.get("width", 3)
    parts = [
        f'<line x1="{x1}" y1="{y1}"'
        f' x2="{x2}" y2="{y2}"'
        f' stroke="{stroke}" stroke-width="{width}"'
    ]
    if "dash" in kw:
        parts.append(f' stroke-dasharray="{kw["dash"]}"')
    if "marker" in kw:
        parts.append(f' marker-end="url(#{kw["marker"]})"')
    parts.append('/>')
    return "".join(parts)


def _text(x, y, content, **kw):
    size = kw.get("size", 18)
    fill = kw.get("fill", "#222")
    anchor = f' text-anchor="{kw["anchor"]}"' if "anchor" in kw else ""
    return (
        f'<text x="{x}" y="{y}"'
        f' font-size="{size}" font-family="Arial"'
        f' fill="{fill}"{anchor}>'
        f'{content}</text>'
    )


def place_label(x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    adx, ady = abs(dx), abs(dy)
    if adx >= ady:
        if dx >= 0:
            return x2 + 8, y2 - 16, "start"
        return x2 - 8, y2 - 16, "end"
    if dy <= 0:
        return x2 + 16, y2 + 5, "start"
    return x2 + 16, y2 + 24, "start"


def _force_arrow(f):
    s, e = f["start"], f["end"]
    x1, y1 = s["x"], s["y"]
    x2, y2 = e["x"], e["y"]
    label = f["label"]
    style = f.get("style", "solid")
    lx, ly, anchor = place_label(x1, y1, x2, y2)
    kwargs = {"marker": "ah"}
    if style == "dashed":
        kwargs["dash"] = "6,4"
    line = _line(x1, y1, x2, y2, **kwargs)
    txt = _text(lx, ly, label, anchor=anchor)
    return f"{line}\n{txt}"


def _render_block(layout):
    parts = []
    parts.append(
        '<rect x="348" y="248" width="104" height="104"'
        ' fill="none" stroke="#222" stroke-width="3" rx="4"/>'
    )
    parts.append(_text(CX, CY + 6, "m", anchor="middle", size=20))
    for f in layout["forces"]:
        parts.append(_force_arrow(f))
    return "\n".join(parts)


def _inclined_plane_base(parts):
    x1, y1 = _INCLINE_START
    x2, y2 = _INCLINE_END
    wedge = f'<polygon points="{x1},{y1} {x2},{y1} {x2},{y2}"'
    wedge += ' fill="#f5f5f5" stroke="#222" stroke-width="2"/>'
    parts.append(wedge)
    parts.append(_line(x1, y1, x2, y2, width=4))
    block_size = 75
    cx_block, cy_block = CX, CY - 24
    rx = cx_block - block_size / 2
    ry = cy_block - block_size / 2
    rot_center = f"{cx_block} {cy_block}"
    parts.append(
        f'<rect x="{rx}" y="{ry}" width="{block_size}" height="{block_size}"'
        f' fill="none" stroke="#222" stroke-width="3" rx="4"'
        f' transform="rotate({_INCLINE_ANGLE:.1f} {rot_center})"/>'
    )
    parts.append(_text(CX, CY - 18, "m", anchor="middle", size=19))
    arc_r = 35
    end_angle = math.radians(-_INCLINE_ANGLE)
    ax2 = x1 + arc_r * math.cos(end_angle)
    ay2 = y1 - arc_r * math.sin(end_angle)
    parts.append(
        f'<path d="M {x1 + arc_r} {y1} A {arc_r} {arc_r} 0 0 0 {ax2:.1f} {ay2:.1f}"'
        f' fill="none" stroke="#222" stroke-width="2"/>'
    )
    parts.append(_text(x1 + arc_r + 8, y1 - 6, "\u03b8", size=16))


def _render_inclined_plane(layout):
    parts = []
    _inclined_plane_base(parts)

    for f in layout["forces"]:
        parts.append(_force_arrow(f))

    mg_tip_x = CX
    mg_tip_y = CY + 130
    comp_len = 90
    mgcos_x = mg_tip_x + _NX * comp_len
    mgcos_y = mg_tip_y + _NY * comp_len
    mgsin_x = mg_tip_x - _UX * comp_len * 0.8
    mgsin_y = mg_tip_y - _UY * comp_len * 0.8

    parts.append(_line(mg_tip_x, mg_tip_y, mgcos_x, mgcos_y, dash="5,3", width=2, marker="ah-gray"))
    lx, ly, _ = place_label(mg_tip_x, mg_tip_y, mgcos_x, mgcos_y)
    parts.append(_text(lx + 6, ly, "mg cos\u03b8", size=14, fill="#666"))

    parts.append(_line(mg_tip_x, mg_tip_y, mgsin_x, mgsin_y, dash="5,3", width=2, marker="ah-gray"))
    lx2, ly2, _ = place_label(mg_tip_x, mg_tip_y, mgsin_x, mgsin_y)
    parts.append(_text(lx2 + 4, ly2, "mg sin\u03b8", size=14, fill="#666"))

    return "\n".join(parts)


def _render_hanging_mass(layout):
    parts = []
    parts.append(_line(CX, 80, CX, 250))
    parts.append(
        f'<circle cx="{CX}" cy="{CY}" r="50"'
        ' fill="none" stroke="#222" stroke-width="3"/>'
    )
    parts.append(_text(CX, CY + 6, "m", anchor="middle", size=20))
    for f in layout["forces"]:
        parts.append(_force_arrow(f))
    return "\n".join(parts)


def _render_magnetic_dipole(layout):
    parts = []
    parts.append(
        '<rect x="235" y="230" width="45" height="140" fill="#d44" rx="3"/>'
    )
    parts.append(_text(257, 220, "N", anchor="middle", size=22, fill="#222"))
    parts.append(
        '<rect x="520" y="230" width="45" height="140" fill="#4488cc" rx="3"/>'
    )
    parts.append(_text(542, 220, "S", anchor="middle", size=22, fill="#222"))

    parts.append(_line(280, 260, 520, 260, dash="8,4", width=2))
    parts.append(_line(280, 300, 520, 300, dash="8,4", width=2))
    parts.append(_line(280, 340, 520, 340, dash="8,4", width=2))

    parts.append(_line(280, 180, 520, 180, width=2, marker="ah"))
    parts.append(_text(CX, 172, "B", anchor="middle", size=18))

    coil_w, coil_h = 90, 150
    cx_coil, cy_coil = CX, CY
    parts.append(
        f'<rect x="{cx_coil - coil_w/2}" y="{cy_coil - coil_h/2}"'
        f' width="{coil_w}" height="{coil_h}" fill="none" stroke="#222" stroke-width="3" rx="3"/>'
    )

    parts.append(_line(355, CY, 355, 130, marker="ah"))
    parts.append(_text(345, 128, "F", anchor="end", size=18))
    parts.append(_line(445, CY, 445, 470, marker="ah"))
    parts.append(_text(455, 478, "F", anchor="start", size=18))

    parts.append(
        '<path d="M 485 210 A 65 65 0 0 1 515 270"'
        ' fill="none" stroke="#222" stroke-width="2" marker-end="url(#ah)"/>'
    )
    parts.append(_text(520, 238, "\u03c4", size=18))

    parts.append(
        f'<line x1="{CX}" y1="{cy_coil - coil_h/2 - 10}"'
        f' x2="{CX}" y2="{cy_coil + coil_h/2 + 10}"'
        ' stroke="#222" stroke-width="1.5" stroke-dasharray="4,4"/>'
    )
    parts.append(
        _text(CX + 10, cy_coil + coil_h / 2 + 25, "Axis", size=14, fill="#666")
    )

    return "\n".join(parts)


def _render_lift(layout):
    parts = []
    parts.append(
        '<rect x="290" y="60" width="220" height="480"'
        ' fill="none" stroke="#bbb" stroke-width="2" rx="4"/>'
    )

    parts.append(_line(CX, 0, CX, 180, width=3))

    cab_w, cab_h = 140, 150
    cab_x = CX - cab_w / 2
    cab_y = CY - cab_h / 2
    parts.append(
        f'<rect x="{cab_x}" y="{cab_y}" width="{cab_w}" height="{cab_h}"'
        ' fill="none" stroke="#222" stroke-width="3" rx="4"/>'
    )

    door_x = CX
    parts.append(
        f'<line x1="{door_x}" y1="{cab_y + 4}"'
        f' x2="{door_x}" y2="{cab_y + cab_h - 4}"'
        ' stroke="#222" stroke-width="1.5"/>'
    )

    parts.append(_text(CX, CY + 6, "m", anchor="middle", size=20))
    for f in layout["forces"]:
        parts.append(_force_arrow(f))
    return "\n".join(parts)


def _render_inclined_plane_friction(layout):
    parts = []
    _inclined_plane_base(parts)
    for f in layout["forces"]:
        parts.append(_force_arrow(f))
    return "\n".join(parts)


def _render_two_body_pulley(layout):
    parts = []
    parts.append(
        f'<circle cx="{CX}" cy="120" r="30"'
        ' fill="none" stroke="#222" stroke-width="3"/>'
    )
    parts.append(
        f'<circle cx="{CX}" cy="120" r="24"'
        ' fill="none" stroke="#222" stroke-width="1.5" stroke-dasharray="3,3"/>'
    )
    parts.append(f'<circle cx="{CX}" cy="120" r="5" fill="#222"/>')
    parts.append(_line(CX, 0, CX, 90, width=3))

    left_x, right_x = 270, 530
    mass_w, mass_h = 65, 65
    mass_y = 245

    parts.append(
        f'<path d="M {left_x} {mass_y} L {CX - 30} 120'
        f' A 30 30 0 0 1 {CX + 30} 120'
        f' L {right_x} {mass_y}"'
        ' fill="none" stroke="#222" stroke-width="2.5"/>'
    )

    parts.append(
        f'<rect x="{left_x - mass_w/2}" y="{mass_y}"'
        f' width="{mass_w}" height="{mass_h}"'
        ' fill="none" stroke="#222" stroke-width="3" rx="4"/>'
    )
    parts.append(
        _text(left_x, mass_y + mass_h / 2 + 6, "m", anchor="middle", size=19)
    )

    parts.append(
        f'<rect x="{right_x - mass_w/2}" y="{mass_y}"'
        f' width="{mass_w}" height="{mass_h}"'
        ' fill="none" stroke="#222" stroke-width="3" rx="4"/>'
    )
    parts.append(
        _text(right_x, mass_y + mass_h / 2 + 6, "m", anchor="middle", size=19)
    )

    mass_cy = mass_y + mass_h / 2
    parts.append(
        _line(left_x, mass_y, left_x, mass_y - 70, marker="ah")
    )
    parts.append(
        _text(left_x - 8, mass_y - 72, "T", anchor="end", size=18)
    )
    parts.append(
        _line(left_x, mass_y + mass_h, left_x, mass_y + mass_h + 75, marker="ah")
    )
    parts.append(
        _text(left_x - 8, mass_y + mass_h + 82, "mg", anchor="end", size=18)
    )
    parts.append(
        _line(right_x, mass_y, right_x, mass_y - 70, marker="ah")
    )
    parts.append(
        _text(right_x + 8, mass_y - 72, "T", anchor="start", size=18)
    )
    parts.append(
        _line(right_x, mass_y + mass_h, right_x, mass_y + mass_h + 75, marker="ah")
    )
    parts.append(
        _text(right_x + 8, mass_y + mass_h + 82, "mg", anchor="start", size=18)
    )
    return "\n".join(parts)


RENDERERS = {
    "block": _render_block,
    "inclined_plane": _render_inclined_plane,
    "hanging_mass": _render_hanging_mass,
    "magnetic_dipole": _render_magnetic_dipole,
    "lift": _render_lift,
    "inclined_plane_friction": _render_inclined_plane_friction,
    "two_body_pulley": _render_two_body_pulley,
}


def render_svg(layout):
    obj_type = layout["object_type"]
    render_fn = RENDERERS.get(obj_type, _render_block)
    body = render_fn(layout)
    return f"{_svg_start()}\n{body}\n{_svg_end()}"


def main():
    with open(BLUEPRINT_FILE, "r", encoding="utf-8") as f:
        blueprints = json.load(f)

    print()
    print("FREE BODY RENDER REPORT")
    print("=" * 60)

    for bp in blueprints:
        layout = generate_layout(bp)
        svg = render_svg(layout)
        output_file = OUTPUT_DIR / f"{bp['question_id']}.svg"
        output_file.write_text(svg, encoding="utf-8")
        print()
        print(bp["question_id"])
        print(output_file)

    print()


if __name__ == "__main__":
    main()
