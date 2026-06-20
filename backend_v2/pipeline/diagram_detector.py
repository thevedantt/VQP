"""
Diagram detection (Phase 3A/3B) - detection only, never generation.

Deliberately NOT the real pipeline (classifier / schema_router /
blueprint_generator / blueprint_evaluator / compiler_router) - those are
out of scope until diagram integration. This is a lightweight keyword
heuristic used only:

    1. as a fallback when a PYQ candidate is missing `diagram_required`
       (the labeled datasets always carry it, so this rarely fires), and
    2. to assign a `diagram_family` (ray / circuit / fbd / magnetic /
       semiconductor / graph) to every diagram_required question, PYQ or
       AI-generated, purely from keywords in the question text - so the
       quota tracking / selection report has something to count without
       running the real classifier.
"""

DIAGRAM_KEYWORDS = (
    "draw", "diagram", "graph", "sketch", "plot", "ray diagram",
    "circuit diagram", "label the", "figure shows", "shown in the figure",
    "shown in figure", "as shown in the figure",
)

# Order matters: first matching family wins, so more specific cues
# (e.g. "free body diagram") are listed before generic ones ("graph").
FAMILY_KEYWORDS = [
    ("fbd", (
        "free body diagram", "free-body diagram", "normal reaction",
        "inclined plane", "block placed on", "friction force acting",
    )),
    ("ray", (
        "ray diagram", "convex lens", "concave lens", "convex mirror",
        "concave mirror", "refraction", "lens formula", "image formed",
        "mirror formula", "optical", "prism", "totally internally reflect",
    )),
    # Checked before "circuit": semiconductor devices (diode, PN junction,
    # bias, transistor, LED, photodiode, solar cell) take priority even
    # when the question also mentions a battery/resistor in the same
    # circuit - they're nonlinear semiconductor devices, never plain
    # circuit components.
    ("semiconductor", (
        "v-i characteristic", "v-i characteristics", "p-n junction",
        "pn junction", "zener diode", "zener", "photodiode", "led",
        "transistor", "energy band diagram", "diode", "forward bias",
        "reverse bias", "forward biasing", "reverse biasing", "solar cell",
    )),
    ("circuit", (
        "circuit diagram", "wheatstone bridge", "potentiometer",
        "ammeter", "voltmeter", "resistor", "rectifier", "transistor circuit",
        "kirchhoff", "cell of emf", "connected in series", "connected in parallel",
    )),
    ("magnetic", (
        "magnetic field", "magnetic field lines", "solenoid",
        "current-carrying conductor", "current carrying conductor",
        "bar magnet", "field due to a", "ampere's circuital law",
    )),
    ("graph", (
        "graph", "plot", "variation of", "v-t graph", "i-t graph", "curve",
    )),
]


def detect_diagram_required(text):
    """Lightweight fallback only - real datasets already carry the flag."""
    lowered = (text or "").lower()
    return any(kw in lowered for kw in DIAGRAM_KEYWORDS)


def detect_diagram_family(text):
    """Best-effort family guess from keywords. Returns None if undetermined."""
    lowered = (text or "").lower()
    for family, keywords in FAMILY_KEYWORDS:
        if any(kw in lowered for kw in keywords):
            return family
    return None
