
import json
import math
from pathlib import Path

from mf_layout import generate_layout
from mf_field_engine import generate_field


BLUEPRINT_FILE = (
    Path(__file__).parent /
    "mf_blueprints.json"
)

OUTPUT_DIR = (
    Path(__file__).parent /
    "output1"
)

OUTPUT_DIR.mkdir(exist_ok=True)


def svg_header():
    return """
    <svg xmlns="http://www.w3.org/2000/svg"
         width="800" height="600"
         font-family="Arial, sans-serif">
      <defs>
        <marker id="arrow" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto" markerUnits="strokeWidth">
          <polygon points="0 0, 10 3.5, 0 7" fill="black"/>
        </marker>
        <marker id="arrowSmall" markerWidth="8" markerHeight="6"
                refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
          <polygon points="0 0, 8 3, 0 6" fill="black"/>
        </marker>
        <marker id="arrowBlue" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto" markerUnits="strokeWidth">
          <polygon points="0 0, 10 3.5, 0 7" fill="#1976d2"/>
        </marker>
        <g id="dot">
          <circle cx="0" cy="0" r="6" fill="none" stroke="black" stroke-width="1.5"/>
          <circle cx="0" cy="0" r="2.5" fill="black"/>
        </g>
        <g id="cross">
          <circle cx="0" cy="0" r="6" fill="none" stroke="black" stroke-width="1.5"/>
          <line x1="-4" y1="-4" x2="4" y2="4" stroke="black" stroke-width="1.5"/>
          <line x1="-4" y1="4" x2="4" y2="-4" stroke="black" stroke-width="1.5"/>
        </g>
      </defs>
      <rect width="100%" height="100%" fill="white"/>
    """


def svg_footer():
    return "    </svg>"


def polyline_svg(points):
    pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f"""
    <polyline points="{pts_str}"
              fill="none"
              stroke="black"
              stroke-width="1.5"/>
    """


def circle_arc(cx, cy, r, start_deg=15, end_deg=345, n=60):
    start = math.radians(start_deg)
    end = math.radians(end_deg)
    if end <= start:
        end += 2 * math.pi
    pts = []
    for i in range(n + 1):
        t = start + (end - start) * i / n
        x = cx + r * math.cos(t)
        y = cy + r * math.sin(t)
        pts.append((x, y))
    pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f"""
    <polyline points="{pts_str}"
              fill="none"
              stroke="black"
              stroke-width="1.5"
              marker-end="url(#arrowSmall)"/>
    """


def arrow_at(x, y, angle_deg, size=8):
    a = math.radians(angle_deg)
    hw = size * 0.35
    tip_x = x
    tip_y = y
    lx = x - size * math.cos(a) + hw * math.sin(a)
    ly = y - size * math.sin(a) - hw * math.cos(a)
    rx = x - size * math.cos(a) - hw * math.sin(a)
    ry = y - size * math.sin(a) + hw * math.cos(a)
    return f"""
    <polygon points="{tip_x:.1f},{tip_y:.1f} {lx:.1f},{ly:.1f} {rx:.1f},{ry:.1f}"
             fill="black"/>
    """


# =====================================================
# M1
# =====================================================

def render_straight_conductor():
    data = generate_field("straight_conductor")
    field_lines = data["field_lines"]

    svg = ""
    for line in field_lines:
        r = int(abs(line[0][0] - 400))
        svg += circle_arc(400, 300, r, start_deg=15, end_deg=345)

    svg += """
    <line x1="400" y1="120" x2="400" y2="480"
          stroke="black" stroke-width="4"/>

    <use href="#dot" x="400" y="300"/>

    <text x="393" y="105" font-size="16" font-weight="bold">I</text>
"""
    return svg


# =====================================================
# M2
# =====================================================

def render_circular_loop():
    data = generate_field("circular_loop")
    cx, cy = data["loop_center"]
    r = data["loop_radius"]
    ax1, ax2 = data["axis"]

    svg = f"""
    <circle cx="{cx}" cy="{cy}" r="{r}"
            fill="none" stroke="black" stroke-width="3"/>

    <line x1="{ax1[0]}" y1="{ax1[1]}"
          x2="{ax2[0]}" y2="{ax2[1]}"
          stroke="black" stroke-dasharray="6,4" stroke-width="2"
          marker-end="url(#arrow)"/>

    <text x="390" y="{cy - r - 30}" font-size="16"
          font-weight="bold">I</text>
    <text x="415" y="{cy + 30}" font-size="16" font-style="italic">μ</text>
    <text x="415" y="{cy - r - 5}" font-size="14" font-weight="bold" fill="#1976d2">N</text>
    <text x="415" y="{cy + r + 20}" font-size="14" font-weight="bold" fill="#d32f2f">S</text>
"""
    for angle in [45, 135, 225, 315]:
        x = cx + r * math.cos(math.radians(angle))
        y = cy + r * math.sin(math.radians(angle))
        svg += arrow_at(x, y, angle + 90, 7)

    return svg


# =====================================================
# M3
# =====================================================

def render_solenoid():
    data = generate_field("solenoid")
    field_lines = data["field_lines"]
    north = data["north"]
    south = data["south"]

    svg = ""

    xs = list(range(200, 621, 40))
    for x in xs:
        svg += f"""
        <circle cx="{x}" cy="300" r="30"
                fill="none" stroke="black" stroke-width="1.5"/>
"""

    for i in range(len(xs) - 1):
        x1, x2 = xs[i], xs[i + 1]
        svg += f"""
        <line x1="{x1 + 12}" y1="270" x2="{x2 - 12}" y2="270"
              stroke="black" stroke-width="1.5"/>
        <line x1="{x1 + 12}" y1="330" x2="{x2 - 12}" y2="330"
              stroke="black" stroke-width="1.5"/>
"""

    for line in field_lines:
        pts_str = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in line)
        svg += f"""
        <polyline points="{pts_str}"
                  fill="none"
                  stroke="black"
                  stroke-width="1.5"
                  marker-end="url(#arrow)"/>
"""

    svg += """
    <path d="M 620 260 Q 400 80 180 260"
          fill="none" stroke="black" stroke-width="1.5"
          marker-end="url(#arrowSmall)"/>
    <path d="M 620 340 Q 400 520 180 340"
          fill="none" stroke="black" stroke-width="1.5"
          marker-end="url(#arrowSmall)"/>
"""

    svg += f"""
    <text x="{south[0]-30}" y="{south[1]+5}" font-size="18"
          font-weight="bold" fill="#d32f2f">S</text>
    <text x="{north[0]+10}" y="{north[1]+5}" font-size="18"
          font-weight="bold" fill="#1976d2">N</text>
"""
    return svg


# =====================================================
# M4
# =====================================================

def render_bar_magnet():
    data = generate_field("bar_magnet")
    field_lines = data["field_lines"]

    svg = ""

    for line in field_lines:
        svg += polyline_svg(line)
        r = int(abs(line[0][0] - 400))
        svg += arrow_at(400, 300 - r, 0, 8)
        svg += arrow_at(400, 300 + r, 0, 8)
        a45 = r * math.cos(math.radians(45))
        a135 = r * math.cos(math.radians(135))
        svg += arrow_at(400 + a45, 300 - r * math.sin(math.radians(45)), -45, 7)
        svg += arrow_at(400 + a135, 300 - r * math.sin(math.radians(135)), 45, 7)

    svg += """
    <rect x="250" y="260" width="300" height="80"
          fill="#f5f5f5" stroke="black" stroke-width="2"/>

    <text x="285" y="305" font-size="18"
          font-weight="bold" fill="#1976d2">N</text>
    <text x="505" y="305" font-size="18"
          font-weight="bold" fill="#d32f2f">S</text>
"""
    return svg


# =====================================================
# M5
# =====================================================

def render_earth_field():
    data = generate_field("earth_magnetism")
    cx, cy = data["earth_center"]
    r = data["radius"]
    ax1, ax2 = data["magnetic_axis"]

    tilt = math.radians(11)
    vx1 = ax1[0] - cx
    vy1 = ax1[1] - cy
    vx2 = ax2[0] - cx
    vy2 = ax2[1] - cy
    max1 = (cx + vx1 * math.cos(tilt) - vy1 * math.sin(tilt),
            cy + vx1 * math.sin(tilt) + vy1 * math.cos(tilt))
    max2 = (cx + vx2 * math.cos(tilt) - vy2 * math.sin(tilt),
            cy + vx2 * math.sin(tilt) + vy2 * math.cos(tilt))

    svg = f"""
    <circle cx="{cx}" cy="{cy}" r="{r}"
            fill="#e3f2fd" stroke="black" stroke-width="2"/>

    <line x1="{cx}" y1="{cy - r - 30}" x2="{cx}" y2="{cy + r + 30}"
          stroke="black" stroke-width="2"/>
    <polygon points="{cx},{cy - r - 30 + 12} {cx - 8},{cy - r - 30 + 25} {cx + 8},{cy - r - 30 + 25}"
             fill="black"/>

    <line x1="{max1[0]:.1f}" y1="{max1[1]:.1f}"
          x2="{max2[0]:.1f}" y2="{max2[1]:.1f}"
          stroke="black" stroke-dasharray="8,4" stroke-width="2"
          marker-end="url(#arrow)"/>

    <path d="M 400 415 A 115 115 0 0 1 {max2[0]:.1f} {max2[1]:.1f}"
          fill="none" stroke="black" stroke-width="1" stroke-dasharray="3,2"/>
    <text x="415" y="440" font-size="12" font-style="italic">~11°</text>

    <line x1="400" y1="300" x2="400" y2="220"
          stroke="#1976d2" stroke-width="2.5"
          marker-end="url(#arrowBlue)"/>
    <text x="405" y="215" font-size="14" font-style="italic" fill="#1976d2">m</text>

    <text x="{cx + 10}" y="{cy - r - 10}" font-size="14"
          font-weight="bold">Geographic N</text>
    <text x="{cx + 10}" y="{cy - r + 35}" font-size="14"
          fill="#1976d2" font-weight="bold">Magnetic N</text>
    <text x="{max2[0]:.1f}" y="{max2[1] + 10:.1f}" font-size="14"
          fill="#d32f2f">Magnetic S</text>
"""
    return svg


# =====================================================
# M6
# =====================================================

def render_current_loop():
    svg = """
    <circle cx="400" cy="300" r="120"
            fill="none" stroke="black" stroke-width="3"/>

    <line x1="400" y1="150" x2="400" y2="450"
          stroke="black" stroke-dasharray="6,4" stroke-width="2"
          marker-end="url(#arrow)"/>

    <text x="415" y="220" font-size="16" font-style="italic">μ</text>
    <text x="390" y="165" font-size="14">I</text>
"""
    for angle in [45, 135, 225, 315]:
        x = 400 + 120 * math.cos(math.radians(angle))
        y = 300 + 120 * math.sin(math.radians(angle))
        svg += arrow_at(x, y, angle + 90, 7)
    return svg


# =====================================================
# M7
# =====================================================

def render_uniform_field():
    svg = ""
    y = 180
    while y <= 420:
        svg += f"""
        <line x1="200" y1="{y}" x2="580" y2="{y}"
              stroke="black" stroke-width="1.5"
              marker-end="url(#arrow)"/>
"""
        y += 40
    return svg


# =====================================================
# M8
# =====================================================

def render_charged_particle():
    return """
    <circle cx="400" cy="300" r="80"
            fill="none" stroke="black" stroke-width="1"
            stroke-dasharray="4,3"/>

    <circle cx="400" cy="300" r="16"
            fill="none" stroke="black" stroke-width="2"/>
    <text x="394" y="305" font-size="18" font-weight="bold">+</text>

    <line x1="400" y1="300" x2="500" y2="300"
          stroke="black" stroke-width="2"
          marker-end="url(#arrow)"/>
    <text x="505" y="295" font-size="14" font-style="italic">v</text>

    <line x1="400" y1="300" x2="400" y2="200"
          stroke="#1976d2" stroke-width="2"
          marker-end="url(#arrowBlue)"/>
    <text x="405" y="195" font-size="14" font-style="italic" fill="#1976d2">B</text>

    <line x1="400" y1="300" x2="320" y2="300"
          stroke="#d32f2f" stroke-width="2"
          marker-end="url(#arrow)"/>
    <text x="310" y="295" font-size="14" font-style="italic" fill="#d32f2f">F</text>
    """


# =====================================================
# M9
# =====================================================

def render_velocity_selector():
    svg = """
    <rect x="240" y="160" width="320" height="280"
          fill="none" stroke="black" stroke-width="2"/>

    <text x="385" y="145" font-size="15" font-weight="bold">Velocity Selector</text>
"""
    for ex in [290, 340, 390, 440, 490]:
        svg += f"""
        <line x1="{ex}" y1="200" x2="{ex}" y2="250"
              stroke="black" stroke-width="1.5"
              marker-end="url(#arrow)"/>
"""
    svg += """
    <text x="250" y="230" font-size="14" font-style="italic">E</text>
"""
    for bx in [290, 340, 390, 440, 490]:
        by = 340
        svg += f"""
        <line x1="{bx-5}" y1="{by-5}" x2="{bx+5}" y2="{by+5}"
              stroke="black" stroke-width="1.5"/>
        <line x1="{bx-5}" y1="{by+5}" x2="{bx+5}" y2="{by-5}"
              stroke="black" stroke-width="1.5"/>
"""
    svg += """
    <text x="250" y="350" font-size="14" font-style="italic">B</text>

    <line x1="100" y1="300" x2="220" y2="300"
          stroke="black" stroke-width="2"
          marker-end="url(#arrow)"/>
    <text x="225" y="295" font-size="14" font-style="italic">v</text>

    <circle cx="240" cy="300" r="10"
            fill="none" stroke="black" stroke-width="1.5"/>
    <text x="237" y="304" font-size="12" font-weight="bold">+</text>
"""
    return svg


# =====================================================
# M10
# =====================================================

def render_cyclotron():
    svg = """
    <path d="M 400 130
             A 170 170 0 0 0 400 470
             L 400 130 Z"
          fill="none" stroke="black" stroke-width="2"/>

    <path d="M 400 130
             A 170 170 0 0 1 400 470
             L 400 130 Z"
          fill="none" stroke="black" stroke-width="2"/>

    <line x1="390" y1="130" x2="390" y2="300"
          stroke="black" stroke-width="0.8" stroke-dasharray="2,3"/>
    <line x1="410" y1="130" x2="410" y2="300"
          stroke="black" stroke-width="0.8" stroke-dasharray="2,3"/>
    <line x1="390" y1="300" x2="390" y2="470"
          stroke="black" stroke-width="0.8" stroke-dasharray="2,3"/>
    <line x1="410" y1="300" x2="410" y2="470"
          stroke="black" stroke-width="0.8" stroke-dasharray="2,3"/>

    <text x="335" y="305" font-size="18" font-weight="bold">D1</text>
    <text x="445" y="305" font-size="18" font-weight="bold">D2</text>

    <path d="M 400 300
             A 20 20 0 0 1 420 300
             A 40 40 0 0 0 380 300
             A 60 60 0 0 1 440 300
             A 80 80 0 0 0 360 300
             A 100 100 0 0 1 460 300
             A 120 120 0 0 0 340 300
             A 140 140 0 0 1 480 300"
          fill="none" stroke="#1976d2" stroke-width="1.5"/>

    <text x="620" y="140" font-size="14" font-style="italic">B</text>
    <text x="180" y="140" font-size="14" font-style="italic">B</text>
"""
    return svg


# =====================================================
# MAIN RENDERER
# =====================================================

def render_svg(layout):
    object_type = layout["object_type"]
    svg = svg_header()
    if object_type == "straight_conductor":
        svg += render_straight_conductor()
    elif object_type == "circular_loop":
        svg += render_circular_loop()
    elif object_type == "solenoid":
        svg += render_solenoid()
    elif object_type == "bar_magnet":
        svg += render_bar_magnet()
    elif object_type == "earth_magnetism":
        svg += render_earth_field()
    elif object_type == "current_loop":
        svg += render_current_loop()
    elif object_type == "uniform_field":
        svg += render_uniform_field()
    elif object_type == "charged_particle":
        svg += render_charged_particle()
    elif object_type == "velocity_selector":
        svg += render_velocity_selector()
    elif object_type == "cyclotron":
        svg += render_cyclotron()
    svg += svg_footer()
    return svg


def main():
    with open(BLUEPRINT_FILE, "r", encoding="utf-8") as f:
        blueprints = json.load(f)
    print()
    print("MAGNETIC FIELD RENDER REPORT")
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
