import json
from pathlib import Path

from semi_layout import generate_layout


BLUEPRINT_FILE = (
    Path(__file__).parent /
    "semi_blueprints.json"
)

OUTPUT_DIR = (
    Path(__file__).parent /
    "output"
)

OUTPUT_DIR.mkdir(exist_ok=True)


def svg_header():

    return """
    <svg xmlns="http://www.w3.org/2000/svg"
         width="800" height="600">
    <style>
      .bg { fill: #ffffff; }
      .title { font: bold 22px Arial,Helvetica,sans-serif; fill: #1a1a1a; }
      .lbl { font: bold 18px Arial,Helvetica,sans-serif; fill: #1a1a1a; }
      .lbl-sm { font: 14px Arial,Helvetica,sans-serif; fill: #1a1a1a; }
      .p-reg { fill: #D6EAF8; stroke: #1a1a1a; stroke-width: 2; }
      .n-reg { fill: #FADBD8; stroke: #1a1a1a; stroke-width: 2; }
      .dep { fill: url(#hatch); stroke: #1a1a1a; stroke-width: 2; }
      .dep-s { fill: #E8E8E8; stroke: #1a1a1a; stroke-width: 2; }
      .wire { stroke: #1a1a1a; stroke-width: 2; fill: none; }
      .wire-t { stroke: #1a1a1a; stroke-width: 1.5; fill: none; }
      .sym { stroke: #1a1a1a; stroke-width: 2.5; fill: none; }
      .cr { font: 16px Arial,Helvetica,sans-serif; fill: #1a1a1a; text-anchor: middle; }
      .ion { font: 12px Arial,Helvetica,sans-serif; fill: #888; text-anchor: middle; }
      .gt { stroke: #1a1a1a; stroke-width: 2.5; fill: #F4F4F4; }
      .light { font: 16px Arial,Helvetica,sans-serif; fill: #E67E22; text-anchor: middle; }
    </style>
    <defs>
      <pattern id="hatch" width="8" height="8"
               patternUnits="userSpaceOnUse"
               patternTransform="rotate(45)">
        <line x1="0" y1="0" x2="0" y2="8"
              stroke="#999" stroke-width="1"/>
      </pattern>
      <marker id="arr" viewBox="0 0 10 10"
              refX="9" refY="5"
              markerWidth="7" markerHeight="7"
              orient="auto">
        <path d="M0,1 L9,5 L0,9 Z" fill="#1a1a1a"/>
      </marker>
      <marker id="arr-o" viewBox="0 0 10 10"
              refX="9" refY="5"
              markerWidth="7" markerHeight="7"
              orient="auto">
        <path d="M0,1 L9,5 L0,9 Z"
              fill="none" stroke="#1a1a1a" stroke-width="1.5"/>
      </marker>
      <marker id="arr-l" viewBox="0 0 10 10"
              refX="9" refY="5"
              markerWidth="7" markerHeight="7"
              orient="auto">
        <path d="M0,1 L9,5 L0,9 Z" fill="#E67E22"/>
      </marker>
    </defs>
    <rect class="bg" width="100%" height="100%"/>
    """


def svg_footer():
    return "</svg>"


# =====================================================
# HELPERS
# =====================================================

def _arrow(x1, y1, x2, y2, cls="wire", marker="arr"):
    return (
        f'<line x1="{x1}" y1="{y1}" '
        f'x2="{x2}" y2="{y2}" '
        f'class="{cls}" '
        f'marker-end="url(#{marker})"/>\n'
    )


def _wire(x1, y1, x2, y2, cls="wire"):
    return (
        f'<line x1="{x1}" y1="{y1}" '
        f'x2="{x2}" y2="{y2}" '
        f'class="{cls}"/>\n'
    )


# =====================================================
# S1 – PN JUNCTION (UNBIASED)
# =====================================================

def render_pn_junction():

    return """
    <text class="title" x="400" y="55"
          text-anchor="middle">PN Junction (Unbiased)</text>

    <text class="lbl-sm" x="400" y="80"
          text-anchor="middle">No external bias applied</text>

    <!-- P region -->
    <rect class="p-reg" x="260" y="220" width="130" height="160"/>
    <text class="lbl" x="325" y="310" text-anchor="middle">P</text>

    <text class="cr" x="280" y="260">+</text>
    <text class="cr" x="355" y="255">+</text>
    <text class="cr" x="310" y="345">+</text>
    <text class="cr" x="275" y="305">+</text>
    <text class="cr" x="345" y="340">+</text>
    <text class="cr" x="290" y="355">+</text>

    <!-- N region -->
    <rect class="n-reg" x="410" y="220" width="130" height="160"/>
    <text class="lbl" x="475" y="310" text-anchor="middle">N</text>

    <text class="cr" x="440" y="260">&#x2022;</text>
    <text class="cr" x="505" y="255">&#x2022;</text>
    <text class="cr" x="465" y="345">&#x2022;</text>
    <text class="cr" x="500" y="305">&#x2022;</text>
    <text class="cr" x="520" y="340">&#x2022;</text>

    <!-- Depletion region -->
    <rect class="dep" x="390" y="220" width="20" height="160"/>
    <text class="lbl" x="400" y="205"
          text-anchor="middle">Depletion Layer</text>

    <text class="ion" x="395" y="260">&#x2212;</text>
    <text class="ion" x="405" y="260">+</text>
    <text class="ion" x="395" y="345">&#x2212;</text>
    <text class="ion" x="405" y="345">+</text>
    """


# =====================================================
# S2 – FORWARD BIAS
# =====================================================

def render_forward_bias():

    return """
    <text class="title" x="400" y="55"
          text-anchor="middle">PN Junction – Forward Bias</text>

    <text class="lbl-sm" x="400" y="80"
          text-anchor="middle">P connected to positive terminal</text>

    <!-- Battery -->
    <line class="wire" x1="145" y1="235" x2="185" y2="235"/>
    <line class="wire" x1="155" y1="385" x2="175" y2="385"/>
    <line class="wire" x1="165" y1="235" x2="165" y2="250"/>
    <line class="wire" x1="165" y1="370" x2="165" y2="385"/>
    <text class="lbl" x="138" y="240" text-anchor="end">+</text>
    <text class="lbl" x="138" y="390" text-anchor="end">&#x2212;</text>

    <!-- Wires -->
    <line class="wire" x1="185" y1="235" x2="260" y2="235"/>
    <line class="wire" x1="165" y1="385" x2="165" y2="440"/>
    <line class="wire" x1="165" y1="440" x2="540" y2="440"/>
    <line class="wire" x1="540" y1="440" x2="540" y2="380"/>

    <!-- P region -->
    <rect class="p-reg" x="260" y="220" width="130" height="160"/>
    <text class="lbl" x="325" y="310" text-anchor="middle">P</text>

    <text class="cr" x="280" y="260">+</text>
    <text class="cr" x="355" y="255">+</text>
    <text class="cr" x="310" y="345">+</text>
    <text class="cr" x="275" y="305">+</text>

    <!-- N region -->
    <rect class="n-reg" x="400" y="220" width="140" height="160"/>
    <text class="lbl" x="470" y="310" text-anchor="middle">N</text>

    <text class="cr" x="430" y="260">&#x2022;</text>
    <text class="cr" x="495" y="255">&#x2022;</text>
    <text class="cr" x="460" y="345">&#x2022;</text>
    <text class="cr" x="500" y="305">&#x2022;</text>

    <!-- Reduced depletion -->
    <rect class="dep-s" x="390" y="220" width="10" height="160"/>
    <text class="lbl-sm" x="395" y="205"
          text-anchor="middle">Reduced Depletion</text>

    <!-- Current arrow – conventional I -->
    <line class="wire" x1="270" y1="212" x2="390" y2="212"
          marker-end="url(#arr)"/>
    <text class="lbl-sm" x="330" y="208"
          text-anchor="middle">I (Conventional Current)</text>

    <!-- Electron flow arrow -->
    <line class="wire-t" x1="400" y1="395" x2="280" y2="395"
          marker-end="url(#arr-o)"/>
    <text class="lbl-sm" x="340" y="415"
          text-anchor="middle">Electron Flow</text>
    """


# =====================================================
# S3 – REVERSE BIAS
# =====================================================

def render_reverse_bias():

    return """
    <text class="title" x="400" y="55"
          text-anchor="middle">PN Junction – Reverse Bias</text>

    <text class="lbl-sm" x="400" y="80"
          text-anchor="middle">P connected to negative terminal</text>

    <!-- Battery on right -->
    <line class="wire" x1="615" y1="385" x2="655" y2="385"/>
    <line class="wire" x1="625" y1="235" x2="645" y2="235"/>
    <line class="wire" x1="635" y1="235" x2="635" y2="250"/>
    <line class="wire" x1="635" y1="370" x2="635" y2="385"/>
    <text class="lbl" x="662" y="390" text-anchor="start">+</text>
    <text class="lbl" x="662" y="240" text-anchor="start">&#x2212;</text>

    <!-- Wires -->
    <line class="wire" x1="625" y1="235" x2="390" y2="235"/>
    <line class="wire" x1="635" y1="385" x2="635" y2="440"/>
    <line class="wire" x1="635" y1="440" x2="570" y2="440"/>
    <line class="wire" x1="570" y1="440" x2="570" y2="380"/>

    <!-- P region -->
    <rect class="p-reg" x="260" y="220" width="130" height="160"/>
    <text class="lbl" x="325" y="310" text-anchor="middle">P</text>

    <text class="cr" x="280" y="260">+</text>
    <text class="cr" x="355" y="255">+</text>
    <text class="cr" x="310" y="345">+</text>
    <text class="cr" x="275" y="305">+</text>

    <!-- N region -->
    <rect class="n-reg" x="430" y="220" width="140" height="160"/>
    <text class="lbl" x="500" y="310" text-anchor="middle">N</text>

    <text class="cr" x="460" y="260">&#x2022;</text>
    <text class="cr" x="530" y="255">&#x2022;</text>
    <text class="cr" x="485" y="345">&#x2022;</text>
    <text class="cr" x="520" y="305">&#x2022;</text>

    <!-- Widened depletion -->
    <rect class="dep" x="390" y="220" width="40" height="160"/>
    <text class="lbl" x="410" y="205"
          text-anchor="middle">Widened Depletion</text>

    <text class="ion" x="400" y="260">&#x2212;</text>
    <text class="ion" x="415" y="255">+</text>
    <text class="ion" x="395" y="345">&#x2212;</text>
    <text class="ion" x="420" y="345">+</text>
    <text class="ion" x="410" y="300">+</text>
    <text class="ion" x="405" y="320">&#x2212;</text>

    <!-- Reverse current -->
    <line class="wire-t" x1="330" y1="205" x2="310" y2="205"
          marker-end="url(#arr-o)"/>
    <text class="lbl-sm" x="320" y="195"
          text-anchor="middle">Small reverse current</text>
    """


# =====================================================
# S4 – ZENER DIODE
# =====================================================

def render_zener():

    return """
    <text class="title" x="400" y="55"
          text-anchor="middle">Zener Diode</text>

    <line class="wire" x1="220" y1="300" x2="300" y2="300"/>

    <polygon points="300,240 435,300 300,360"
             class="sym"/>

    <line x1="435" y1="240" x2="460" y2="240"
          class="sym"/>
    <line x1="460" y1="240" x2="435" y2="360"
          class="sym"/>
    <line x1="435" y1="360" x2="460" y2="360"
          class="sym"/>

    <line class="wire" x1="448" y1="300" x2="580" y2="300"/>

    <text class="lbl" x="180" y="305" text-anchor="end">Anode</text>
    <text class="lbl" x="620" y="305" text-anchor="start">Cathode</text>
    """


# =====================================================
# S5 – LED (LIGHT EMITTING DIODE)
# =====================================================

def render_led():

    return """
    <text class="title" x="400" y="55"
          text-anchor="middle">Light Emitting Diode (LED)</text>

    <line class="wire" x1="220" y1="300" x2="300" y2="300"/>

    <polygon points="300,240 440,300 300,360"
             class="sym"/>
    <line x1="440" y1="240" x2="440" y2="360"
          class="sym"/>

    <line class="wire" x1="440" y1="300" x2="580" y2="300"/>

    <line class="wire-t" x1="475" y1="255" x2="550" y2="180"
          marker-end="url(#arr-l)"/>
    <line class="wire-t" x1="485" y1="280" x2="565" y2="210"
          marker-end="url(#arr-l)"/>
    <line class="wire-t" x1="485" y1="320" x2="565" y2="270"
          marker-end="url(#arr-l)"/>
    <line class="wire-t" x1="475" y1="345" x2="550" y2="300"
          marker-end="url(#arr-l)"/>

    <text class="light" x="560" y="175"
          text-anchor="start">Light</text>

    <text class="lbl-sm" x="370" y="420"
          text-anchor="middle">LED</text>
    """


# =====================================================
# S6 – PHOTODIODE
# =====================================================

def render_photodiode():

    return """
    <text class="title" x="400" y="55"
          text-anchor="middle">Photodiode</text>

    <line class="wire" x1="220" y1="300" x2="300" y2="300"/>

    <polygon points="300,240 440,300 300,360"
             class="sym"/>
    <line x1="440" y1="240" x2="440" y2="360"
          class="sym"/>

    <line class="wire" x1="440" y1="300" x2="580" y2="300"/>

    <line class="wire-t" x1="575" y1="175" x2="505" y2="245"
          marker-end="url(#arr-l)"/>
    <line class="wire-t" x1="595" y1="200" x2="520" y2="275"
          marker-end="url(#arr-l)"/>
    <line class="wire-t" x1="595" y1="240" x2="520" y2="310"
          marker-end="url(#arr-l)"/>
    <line class="wire-t" x1="575" y1="280" x2="505" y2="335"
          marker-end="url(#arr-l)"/>

    <text class="light" x="605" y="170"
          text-anchor="end">Incident</text>
    <text class="light" x="605" y="190"
          text-anchor="end">Light</text>
    """


# =====================================================
# S7 – NOT GATE
# =====================================================

def render_not_gate():

    return """
    <text class="title" x="400" y="55"
          text-anchor="middle">NOT Gate (Inverter)</text>

    <polygon points="250,220 250,380 430,300"
             class="gt"/>
    <circle cx="448" cy="300" r="15"
            fill="#F4F4F4" stroke="#1a1a1a" stroke-width="2.5"/>

    <line class="wire" x1="150" y1="300" x2="250" y2="300"/>
    <line class="wire" x1="463" y1="300" x2="600" y2="300"/>

    <text class="lbl" x="130" y="305" text-anchor="end">A</text>
    <text class="lbl" x="620" y="305" text-anchor="start">Y</text>
    """


# =====================================================
# S8 – AND GATE
# =====================================================

def render_and_gate():

    return """
    <text class="title" x="400" y="55"
          text-anchor="middle">AND Gate</text>

    <path d="M 250 220 L 390 220
             A 80 80 0 0 1 390 380
             L 250 380 Z"
          class="gt"/>

    <line class="wire" x1="150" y1="260" x2="250" y2="260"/>
    <line class="wire" x1="150" y1="340" x2="250" y2="340"/>
    <line class="wire" x1="470" y1="300" x2="620" y2="300"/>

    <text class="lbl" x="130" y="265" text-anchor="end">A</text>
    <text class="lbl" x="130" y="345" text-anchor="end">B</text>
    <text class="lbl" x="640" y="305" text-anchor="start">Y</text>
    """


# =====================================================
# S9 – OR GATE
# =====================================================

def render_or_gate():

    return """
    <text class="title" x="400" y="55"
          text-anchor="middle">OR Gate</text>

    <path d="M 240 220
             Q 350 300 240 380
             Q 400 380 510 300
             Q 400 220 240 220"
          class="gt"/>

    <line class="wire" x1="150" y1="260" x2="250" y2="260"/>
    <line class="wire" x1="150" y1="340" x2="250" y2="340"/>
    <line class="wire" x1="510" y1="300" x2="620" y2="300"/>

    <text class="lbl" x="130" y="265" text-anchor="end">A</text>
    <text class="lbl" x="130" y="345" text-anchor="end">B</text>
    <text class="lbl" x="640" y="305" text-anchor="start">Y</text>
    """


# =====================================================
# S10 – NAND GATE
# =====================================================

def render_nand_gate():

    return """
    <text class="title" x="400" y="55"
          text-anchor="middle">NAND Gate</text>

    <path d="M 250 220 L 390 220
             A 80 80 0 0 1 390 380
             L 250 380 Z"
          class="gt"/>
    <circle cx="488" cy="300" r="15"
            fill="#F4F4F4" stroke="#1a1a1a" stroke-width="2.5"/>

    <line class="wire" x1="150" y1="260" x2="250" y2="260"/>
    <line class="wire" x1="150" y1="340" x2="250" y2="340"/>
    <line class="wire" x1="503" y1="300" x2="620" y2="300"/>

    <text class="lbl" x="130" y="265" text-anchor="end">A</text>
    <text class="lbl" x="130" y="345" text-anchor="end">B</text>
    <text class="lbl" x="640" y="305" text-anchor="start">Y</text>
    """


# =====================================================
# MAIN
# =====================================================

def render_svg(layout):

    obj = layout["object_type"]

    svg = svg_header()

    if obj == "pn_junction":
        svg += render_pn_junction()
    elif obj == "forward_bias":
        svg += render_forward_bias()
    elif obj == "reverse_bias":
        svg += render_reverse_bias()
    elif obj == "zener_diode":
        svg += render_zener()
    elif obj == "led":
        svg += render_led()
    elif obj == "photodiode":
        svg += render_photodiode()
    elif obj == "not_gate":
        svg += render_not_gate()
    elif obj == "and_gate":
        svg += render_and_gate()
    elif obj == "or_gate":
        svg += render_or_gate()
    elif obj == "nand_gate":
        svg += render_nand_gate()

    svg += svg_footer()

    return svg


def main():

    with open(
        BLUEPRINT_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        blueprints = json.load(f)

    print()
    print("SEMICONDUCTOR RENDER REPORT")
    print("=" * 60)

    for bp in blueprints:

        layout = generate_layout(bp)

        svg = render_svg(layout)

        output_file = (
            OUTPUT_DIR /
            f"{bp['question_id']}.svg"
        )

        output_file.write_text(
            svg,
            encoding="utf-8"
        )

        print()
        print(bp["question_id"])
        print(output_file)

    print()


if __name__ == "__main__":
    main()
