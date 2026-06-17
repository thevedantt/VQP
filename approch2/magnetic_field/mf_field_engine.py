
from math import cos
from math import sin
from math import pi


# =====================================================
# FIELD LINE UTILITIES
# =====================================================

def circle_points(
    cx,
    cy,
    radius,
    n=60
):

    pts = []

    for i in range(n + 1):

        t = 2 * pi * i / n

        x = cx + radius * cos(t)
        y = cy + radius * sin(t)

        pts.append((x, y))

    return pts


# =====================================================
# M1
# STRAIGHT CONDUCTOR
# =====================================================

def straight_conductor_field():

    field_lines = []

    for r in [40, 70, 100, 130]:

        field_lines.append(
            circle_points(
                400,
                300,
                r
            )
        )

    return {
        "type": "straight_conductor",
        "field_lines": field_lines
    }


# =====================================================
# M2
# CIRCULAR LOOP
# =====================================================

def circular_loop_field():

    return {
        "type": "circular_loop",
        "loop_center": (400, 300),
        "loop_radius": 120,

        "axis": [
            (400, 150),
            (400, 450)
        ]
    }


# =====================================================
# M3
# SOLENOID
# =====================================================

def solenoid_field():

    field_lines = []

    y_values = [
        260,
        300,
        340
    ]

    for y in y_values:

        field_lines.append([
            (180, y),
            (620, y)
        ])

    return {
        "type": "solenoid",
        "field_lines": field_lines,
        "north": (620, 220),
        "south": (180, 220)
    }


# =====================================================
# M4
# BAR MAGNET
# =====================================================

def bar_magnet_field():

    field_lines = []

    radii = [
        90,
        120,
        150,
        180
    ]

    for r in radii:

        field_lines.append(
            circle_points(
                400,
                300,
                r
            )
        )

    return {
        "type": "bar_magnet",
        "field_lines": field_lines
    }


# =====================================================
# M5
# EARTH FIELD
# =====================================================

def earth_field():

    return {
        "type": "earth_field",

        "earth_center": (
            400,
            300
        ),

        "radius": 120,

        "magnetic_axis": [
            (400, 180),
            (400, 420)
        ]
    }


# =====================================================
# DISPATCHER
# =====================================================

def generate_field(object_type):

    if object_type == "straight_conductor":
        return straight_conductor_field()

    if object_type == "circular_loop":
        return circular_loop_field()

    if object_type == "solenoid":
        return solenoid_field()

    if object_type == "bar_magnet":
        return bar_magnet_field()

    if object_type == "earth_magnetism":
        return earth_field()

    return {}


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":

    tests = [

        "straight_conductor",

        "circular_loop",

        "solenoid",

        "bar_magnet",

        "earth_magnetism"
    ]

    print()
    print("MAGNETIC FIELD ENGINE REPORT")
    print("=" * 60)

    for t in tests:

        result = generate_field(t)

        print()
        print(t)
        print(result)

