
# generate_circuit_assets.py

from pathlib import Path


ASSET_DIR = Path("assets")
ASSET_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def save_svg(
    filename: str,
    svg: str
):

    output = ASSET_DIR / filename

    output.write_text(
        svg,
        encoding="utf-8"
    )

    print(
        f"✓ {filename}"
    )


# =====================================================
# C7
# VOLTMETER ACROSS RESISTOR
# =====================================================

def generate_voltmeter_circuit():

    svg = """
<svg xmlns="http://www.w3.org/2000/svg"
     width="700"
     height="300">

<line x1="100" y1="150" x2="220" y2="150"
      stroke="black" stroke-width="2"/>

<rect x="220" y="135"
      width="120"
      height="30"
      fill="none"
      stroke="black"/>

<text x="275" y="130">R</text>

<line x1="340" y1="150"
      x2="500"
      y2="150"
      stroke="black"
      stroke-width="2"/>

<line x1="220" y1="150"
      x2="220"
      y2="70"
      stroke="black"
      stroke-width="2"/>

<line x1="340" y1="150"
      x2="340"
      y2="70"
      stroke="black"
      stroke-width="2"/>

<circle cx="280"
        cy="70"
        r="25"
        fill="none"
        stroke="black"/>

<text x="272" y="77">V</text>

<line x1="220" y1="70"
      x2="255"
      y2="70"
      stroke="black"
      stroke-width="2"/>

<line x1="305" y1="70"
      x2="340"
      y2="70"
      stroke="black"
      stroke-width="2"/>

</svg>
"""
    save_svg(
        "voltmeter_across_resistor.svg",
        svg
    )


# =====================================================
# C9
# WHEATSTONE BRIDGE
# =====================================================

def generate_wheatstone_bridge():

    svg = """
<svg xmlns="http://www.w3.org/2000/svg"
     width="700"
     height="500">

<line x1="200" y1="120"
      x2="350" y2="220"
      stroke="black"
      stroke-width="2"/>

<line x1="350" y1="220"
      x2="500" y2="120"
      stroke="black"
      stroke-width="2"/>

<line x1="200" y1="320"
      x2="350" y2="220"
      stroke="black"
      stroke-width="2"/>

<line x1="350" y1="220"
      x2="500" y2="320"
      stroke="black"
      stroke-width="2"/>

<circle cx="350"
        cy="220"
        r="25"
        fill="none"
        stroke="black"/>

<text x="343" y="227">G</text>

<text x="250" y="150">P</text>
<text x="450" y="150">Q</text>
<text x="250" y="300">R</text>
<text x="450" y="300">S</text>

</svg>
"""
    save_svg(
        "wheatstone_bridge.svg",
        svg
    )


# =====================================================
# C10
# METER BRIDGE
# =====================================================

def generate_meter_bridge():

    svg = """
<svg xmlns="http://www.w3.org/2000/svg"
     width="900"
     height="400">

<line x1="150"
      y1="200"
      x2="750"
      y2="200"
      stroke="black"
      stroke-width="3"/>

<text x="400" y="180">
100 cm wire
</text>

<rect x="180"
      y="120"
      width="100"
      height="30"
      fill="none"
      stroke="black"/>

<text x="220" y="115">R</text>

<rect x="620"
      y="120"
      width="100"
      height="30"
      fill="none"
      stroke="black"/>

<text x="660" y="115">X</text>

<circle cx="450"
        cy="270"
        r="25"
        fill="none"
        stroke="black"/>

<text x="442" y="278">G</text>

<line x1="450"
      y1="200"
      x2="450"
      y2="245"
      stroke="black"
      stroke-width="2"/>

<text x="460" y="195">J</text>

</svg>
"""
    save_svg(
        "meter_bridge.svg",
        svg
    )


# =====================================================
# C11
# POTENTIOMETER
# =====================================================

def generate_potentiometer():

    svg = """
<svg xmlns="http://www.w3.org/2000/svg"
     width="900"
     height="400">

<line x1="150"
      y1="200"
      x2="750"
      y2="200"
      stroke="black"
      stroke-width="3"/>

<text x="420" y="180">
Potentiometer Wire
</text>

<line x1="450"
      y1="120"
      x2="450"
      y2="200"
      stroke="black"
      stroke-width="2"/>

<circle cx="450"
        cy="120"
        r="8"
        fill="black"/>

<text x="465" y="125">
Jockey
</text>

</svg>
"""
    save_svg(
        "potentiometer.svg",
        svg
    )


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    generate_voltmeter_circuit()

    generate_wheatstone_bridge()

    generate_meter_bridge()

    generate_potentiometer()

    print(
        "\nAll circuit assets generated."
    )
