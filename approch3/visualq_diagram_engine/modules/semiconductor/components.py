"""
Reusable semantic components for PN junction semiconductor diagrams.

These builders know physics-level semantics (P region, depletion, N region)
and construct the correct SceneNode objects for NCERT-style rendering.
They are used by the programmatic scene builders (pn_junction.py, forward_bias.py)
as an alternative to the YAML template path.

Each component receives a Layer and calls layer.add() with the appropriate nodes.
"""

from visualq_diagram_engine.core.scene import Layer
from visualq_diagram_engine.primitives.rectangle import Rectangle
from visualq_diagram_engine.primitives.line import Line
from visualq_diagram_engine.primitives.text import Text
from visualq_diagram_engine.primitives.carrier_grid import CarrierGrid
from visualq_diagram_engine.primitives.ion_grid import IonGrid
from visualq_diagram_engine.primitives.field_arrow import FieldArrow
from visualq_diagram_engine.primitives.styles import Style
from visualq_diagram_engine.typography import Typography


class JunctionBody:
    """
    Builds the semiconductor body: very-light P and N tints, a depletion fill,
    and the outer border rectangle — all in NCERT monochrome style.
    """

    def __init__(
        self,
        x: float, y: float,
        p_width: float, n_width: float,
        depletion_width: float,
        height: float,
    ):
        self.x = x
        self.y = y
        self.p_width = p_width
        self.n_width = n_width
        self.depletion_width = depletion_width
        self.height = height

    @property
    def dep_x(self) -> float:
        return self.x + self.p_width

    @property
    def n_x(self) -> float:
        return self.dep_x + self.depletion_width

    @property
    def total_width(self) -> float:
        return self.p_width + self.depletion_width + self.n_width

    def build(self, layer: Layer) -> None:
        # Very light region tints (barely visible — textbook-style)
        layer.add(Rectangle(
            id="p_region_tint",
            position=(self.x, self.y),
            width=self.p_width, height=self.height,
            style=Style(fill="#FFF8F8", stroke="none"),
        ))
        layer.add(Rectangle(
            id="n_region_tint",
            position=(self.n_x, self.y),
            width=self.n_width, height=self.height,
            style=Style(fill="#F8F8FF", stroke="none"),
        ))
        # Depletion region fill
        layer.add(Rectangle(
            id="depletion_fill",
            position=(self.dep_x, self.y),
            width=self.depletion_width, height=self.height,
            style=Style(fill="#F2F2F2", stroke="none"),
        ))
        # Outer semiconductor body border
        layer.add(Rectangle(
            id="semiconductor_body",
            position=(self.x, self.y),
            width=self.total_width, height=self.height,
            style=Style(fill="none", stroke="#000000", stroke_width=1.5),
        ))


class DepletionRegion:
    """
    Adds dashed vertical boundary lines on both edges of the depletion region.
    These distinguish the depletion layer from the bulk semiconductor in NCERT style.
    """

    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def build(self, layer: Layer) -> None:
        dash = Style(stroke="#444444", stroke_width=1.0, dash_array="6,4", fill="none")
        layer.add(Line(
            id="dep_left_boundary",
            position=(self.x, self.y),
            start=(self.x, self.y),
            end=(self.x, self.y + self.height),
            style=dash,
        ))
        layer.add(Line(
            id="dep_right_boundary",
            position=(self.x + self.width, self.y),
            start=(self.x + self.width, self.y),
            end=(self.x + self.width, self.y + self.height),
            style=dash,
        ))


class HoleGrid:
    """Builds a grid of holes (hollow circles with + symbol, NCERT style)."""

    def __init__(
        self,
        x: float, y: float,
        rows: int = 3, cols: int = 3,
        spacing_x: float = 62.0, spacing_y: float = 55.0,
        radius: float = 9.0,
        show_arrows: bool = True,
        arrow_length: float = 20.0,
    ):
        self.x = x
        self.y = y
        self.rows = rows
        self.cols = cols
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y
        self.radius = radius
        self.show_arrows = show_arrows
        self.arrow_length = arrow_length

    def build(self, layer: Layer) -> None:
        layer.add(CarrierGrid(
            id="hole_grid",
            position=(self.x, self.y),
            rows=self.rows, cols=self.cols,
            spacing_x=self.spacing_x, spacing_y=self.spacing_y,
            carrier_type="hole",
            carrier_radius=self.radius,
            show_arrows=self.show_arrows,
            arrow_direction="right",
            arrow_length=self.arrow_length,
            style=Style(stroke="#000000", stroke_width=1.5),
        ))


class ElectronGrid:
    """Builds a grid of electrons (solid black circles, NCERT style)."""

    def __init__(
        self,
        x: float, y: float,
        rows: int = 3, cols: int = 3,
        spacing_x: float = 60.0, spacing_y: float = 55.0,
        radius: float = 7.0,
        show_arrows: bool = True,
        arrow_length: float = 20.0,
    ):
        self.x = x
        self.y = y
        self.rows = rows
        self.cols = cols
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y
        self.radius = radius
        self.show_arrows = show_arrows
        self.arrow_length = arrow_length

    def build(self, layer: Layer) -> None:
        layer.add(CarrierGrid(
            id="electron_grid",
            position=(self.x, self.y),
            rows=self.rows, cols=self.cols,
            spacing_x=self.spacing_x, spacing_y=self.spacing_y,
            carrier_type="electron",
            carrier_radius=self.radius,
            show_arrows=self.show_arrows,
            arrow_direction="left",
            arrow_length=self.arrow_length,
            style=Style(stroke="#000000", stroke_width=1.0),
        ))


class DepletionIonGrid:
    """
    Places fixed ion symbols inside the depletion region:
      - Negative acceptor ions on the P-side (left quarter)
      - Positive donor ions on the N-side (right quarter)

    Replaces manually positioned text nodes.
    """

    def __init__(
        self,
        dep_x: float, dep_width: float,
        dep_y: float, dep_height: float,
        rows: int = 3,
        spacing_y: float = 45.0,
        symbol_size: float = 14.0,
    ):
        self.dep_x = dep_x
        self.dep_width = dep_width
        self.dep_y = dep_y
        self.dep_height = dep_height
        self.rows = rows
        self.spacing_y = spacing_y
        self.symbol_size = symbol_size

    def build(self, layer: Layer) -> None:
        grid_h = (self.rows - 1) * self.spacing_y
        top_y  = self.dep_y + (self.dep_height - grid_h) / 2
        ion_style = Style(
            fill="#000000", stroke="none",
            font_size=self.symbol_size, font_weight="bold",
            text_anchor="middle",
        )
        # Negative ions (P-side of depletion)
        layer.add(IonGrid(
            id="neg_ions",
            position=(self.dep_x + self.dep_width / 4, top_y),
            rows=self.rows, cols=1,
            spacing_y=self.spacing_y,
            charge="negative",
            symbol_size=self.symbol_size,
            style=ion_style,
        ))
        # Positive ions (N-side of depletion)
        layer.add(IonGrid(
            id="pos_ions",
            position=(self.dep_x + self.dep_width * 3 / 4, top_y),
            rows=self.rows, cols=1,
            spacing_y=self.spacing_y,
            charge="positive",
            symbol_size=self.symbol_size,
            style=ion_style,
        ))


class ElectricFieldArrow:
    """
    Renders the built-in electric field arrow inside the depletion region
    using the FieldArrow primitive (arrow + auto-label).

    The internal field (Ei) points from N-side positive ions to P-side
    negative ions — i.e. right-to-left in a standard forward-bias diagram.
    """

    def __init__(
        self,
        dep_x: float, dep_right_x: float, mid_y: float,
        label: str = "Ei",
        margin: float = 10.0,
    ):
        self.dep_x = dep_x
        self.dep_right_x = dep_right_x
        self.mid_y = mid_y
        self.label = label
        self.margin = margin

    def build(self, layer: Layer) -> None:
        sx = self.dep_right_x - self.margin
        ex = self.dep_x + self.margin
        layer.add(FieldArrow(
            id="efield_internal",
            position=(sx, self.mid_y),
            end=(ex, self.mid_y),
            head_size=7,
            label=self.label,
            label_side="above",
            label_offset=12,
            style=Style(
                stroke="#000000", stroke_width=1.2,
                font_size=10, fill="#000000",
                font_family="Arial", text_anchor="middle",
            ),
        ))


class RegionLabel:
    """Creates a text label centred above a semiconductor region."""

    def __init__(
        self, node_id: str, x: float, y: float,
        content: str, font_size: float = 16.0,
    ):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.content = content
        self.font_size = font_size

    def build(self, layer: Layer) -> None:
        layer.add(Text(
            id=self.node_id,
            position=(self.x, self.y),
            content=self.content,
            style=Style(
                fill="#000000", stroke="none",
                font_size=self.font_size,
                font_weight="bold",
                text_anchor="middle",
            ),
        ))
