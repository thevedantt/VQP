import json
from pathlib import Path

from fbd_layout import generate_layout


BLUEPRINT_FILE = Path(__file__).parent / "fbd_blueprints.json"

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SVG_W = 800
SVG_H = 600


def _svg_start():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}">
<defs>
  <marker id="ah" markerWidth="12" markerHeight="8" refX="12" refY="4" orient="auto">
    <polygon points="0,0 12,4 0,8" fill="#222"/>
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


def _label_pos(x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    adx, ady = abs(dx), abs(dy)
    if adx > ady:
        if dx > 0:
            return x2 + 8, y2 - 15, "start"
        return x2 - 8, y2 - 15, "end"
    if dy < 0:
        return x2 + 15, y2 + 6, "start"
    return x2 + 15, y2 + 24, "start"


def _force_arrow(f):
    s, e = f["start"], f["end"]
    x1, y1 = s["x"], s["y"]
    x2, y2 = e["x"], e["y"]
    label = f["label"]
    style = f.get("style", "solid")
    lx, ly, anchor = _label_pos(x1, y1, x2, y2)
    kwargs = {"marker": "ah"}
    if style == "dashed":
        kwargs["dash"] = "6,4"
    line = _line(x1, y1, x2, y2, **kwargs)
    txt = _text(lx, ly, label, anchor=anchor)
    return f"{line}\n{txt}"


def _render_block(layout):
    parts = []
    parts.append(
        '<rect x="350" y="250" width="100" height="100"'
        ' fill="none" stroke="#222" stroke-width="3" rx="4"/>'
    )
    parts.append(_text(400, 310, "m", anchor="middle"))
    for f in layout["forces"]:
        parts.append(_force_arrow(f))
    return "\n".join(parts)


def _render_inclined_plane(layout):
    parts = []
    parts.append(_line(200, 420, 600, 200, width=4))
    parts.append(
        '<rect x="365" y="238" width="70" height="70"'
        ' fill="none" stroke="#222" stroke-width="3" rx="4"'
        ' transform="rotate(-26.565 400 273)"/>'
    )
    parts.append(_text(400, 283, "m", anchor="middle"))
    parts.append(
        '<path d="M 220 410 A 30 30 0 0 0 246 385"'
        ' fill="none" stroke="#222" stroke-width="2"/>'
    )
    parts.append(_text(238, 412, "\u03b8", size=16))
    for f in layout["forces"]:
        parts.append(_force_arrow(f))
    return "\n".join(parts)


def _render_hanging_mass(layout):
    parts = []
    parts.append(_line(400, 100, 400, 250))
    parts.append(
        '<circle cx="400" cy="300" r="50"'
        ' fill="none" stroke="#222" stroke-width="3"/>'
    )
    parts.append(_text(400, 308, "m", anchor="middle"))
    for f in layout["forces"]:
        parts.append(_force_arrow(f))
    return "\n".join(parts)


def _render_magnetic_dipole(layout):
    parts = []
    parts.append(
        '<rect x="240" y="240" width="40" height="120" fill="#cc2222" rx="3"/>'
    )
    parts.append(_text(260, 230, "N", anchor="middle", size=22))
    parts.append(
        '<rect x="520" y="240" width="40" height="120" fill="#2266cc" rx="3"/>'
    )
    parts.append(_text(540, 230, "S", anchor="middle", size=22))
    for y in (260, 300, 340):
        parts.append(_line(280, y, 520, y, dash="8,4", width=2))
    parts.append(
        '<rect x="360" y="230" width="80" height="140"'
        ' fill="none" stroke="#222" stroke-width="3" rx="3"/>'
    )
    parts.append(_line(360, 300, 360, 150, marker="ah"))
    parts.append(_text(350, 148, "F", anchor="end"))
    parts.append(_line(440, 300, 440, 450, marker="ah"))
    parts.append(_text(450, 458, "F", anchor="start"))
    parts.append(
        '<path d="M 480 220 A 60 60 0 0 1 505 280"'
        ' fill="none" stroke="#222" stroke-width="2" marker-end="url(#ah)"/>'
    )
    parts.append(_text(508, 245, "\u03c4", size=18))
    return "\n".join(parts)


def _render_lift(layout):
    parts = []
    parts.append(
        '<rect x="300" y="100" width="200" height="400"'
        ' fill="none" stroke="#999" stroke-width="2" rx="4"/>'
    )
    parts.append(
        '<rect x="340" y="220" width="120" height="120"'
        ' fill="none" stroke="#222" stroke-width="3" rx="4"/>'
    )
    parts.append(_text(400, 282, "m", anchor="middle"))
    for f in layout["forces"]:
        parts.append(_force_arrow(f))
    return "\n".join(parts)


def _render_inclined_plane_friction(layout):
    parts = []
    parts.append(_line(200, 420, 600, 200, width=4))
    parts.append(
        '<rect x="365" y="238" width="70" height="70"'
        ' fill="none" stroke="#222" stroke-width="3" rx="4"'
        ' transform="rotate(-26.565 400 273)"/>'
    )
    parts.append(_text(400, 283, "m", anchor="middle"))
    parts.append(
        '<path d="M 220 410 A 30 30 0 0 0 246 385"'
        ' fill="none" stroke="#222" stroke-width="2"/>'
    )
    parts.append(_text(238, 412, "\u03b8", size=16))
    for f in layout["forces"]:
        parts.append(_force_arrow(f))
    return "\n".join(parts)


def _render_two_body_pulley(layout):
    parts = []
    parts.append(
        '<circle cx="400" cy="120" r="30"'
        ' fill="none" stroke="#222" stroke-width="3"/>'
    )
    parts.append('<circle cx="400" cy="120" r="5" fill="#222"/>')
    parts.append(_line(400, 0, 400, 90, width=2))
    parts.append(_line(400, 120, 280, 250, width=2))
    parts.append(_line(400, 120, 520, 250, width=2))
    parts.append(
        '<rect x="250" y="250" width="60" height="60"'
        ' fill="none" stroke="#222" stroke-width="3" rx="4"/>'
    )
    parts.append(_text(280, 286, "m", anchor="middle"))
    parts.append(
        '<rect x="490" y="250" width="60" height="60"'
        ' fill="none" stroke="#222" stroke-width="3" rx="4"/>'
    )
    parts.append(_text(520, 286, "m", anchor="middle"))
    parts.append(_line(280, 250, 280, 175, marker="ah"))
    parts.append(_text(268, 173, "T", anchor="end"))
    parts.append(_line(280, 310, 280, 385, marker="ah"))
    parts.append(_text(268, 393, "mg", anchor="end"))
    parts.append(_line(520, 250, 520, 175, marker="ah"))
    parts.append(_text(532, 173, "T", anchor="start"))
    parts.append(_line(520, 310, 520, 385, marker="ah"))
    parts.append(_text(532, 393, "mg", anchor="start"))
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
