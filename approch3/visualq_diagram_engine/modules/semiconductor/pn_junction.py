"""
PNJunction — programmatic scene builder for PN junction diagrams.

Uses SemiconductorLayout and CircuitLayout for automatic position calculation.
All geometry is driven by proportions, not magic numbers.

Use this class when generating scenes from Python code rather than YAML.
"""

from visualq_diagram_engine.core.scene import Scene, Layer
from visualq_diagram_engine.primitives.text import Text
from visualq_diagram_engine.primitives.styles import Style
from visualq_diagram_engine.layouts.semiconductor_layout import (
    SemiconductorLayout,
    CircuitLayout,
)
from visualq_diagram_engine.layouts.collision_detector import CollisionDetector
from visualq_diagram_engine.modules.semiconductor.components import (
    JunctionBody,
    DepletionRegion,
    DepletionIonGrid,
    HoleGrid,
    ElectronGrid,
    ElectricFieldArrow,
    RegionLabel,
)
from visualq_diagram_engine.primitives.field_arrow import FieldArrow
from visualq_diagram_engine.primitives.wire_path import WirePath
from visualq_diagram_engine.primitives.battery_symbol import BatterySymbol
from visualq_diagram_engine.primitives.resistor_symbol import ResistorSymbol
from visualq_diagram_engine.primitives.switch_symbol import SwitchSymbol


class PNJunction:
    """
    Base class for programmatic PN junction scene construction.

    Geometry is computed by SemiconductorLayout — no hardcoded coordinates.
    All proportions, margins, and circuit parameters are configurable.
    """

    def __init__(
        self,
        canvas_w: float = 900.0,
        canvas_h: float = 480.0,
        margin_x: float = 85.0,
        margin_y: float = 75.0,
        block_height: float = 165.0,
        p_fraction: float = 0.40,
        dep_fraction: float = 0.14,
        n_fraction: float = 0.46,
        circuit_y: float = 290.0,
        arm_x_margin: float = 42.0,
        switch_length: float = 55.0,
        battery_cells: int = 1,
        battery_gap: float = 18.0,
        resistor_length: float = 80.0,
    ):
        self.layout = SemiconductorLayout(
            canvas_w=canvas_w, canvas_h=canvas_h,
            margin_x=margin_x, margin_y=margin_y,
            block_height=block_height,
            p_fraction=p_fraction,
            dep_fraction=dep_fraction,
            n_fraction=n_fraction,
        )
        self.circ = CircuitLayout(
            semi=self.layout,
            circuit_y=circuit_y,
            arm_x_margin=arm_x_margin,
            switch_length=switch_length,
            battery_cells=battery_cells,
            battery_gap=battery_gap,
            resistor_length=resistor_length,
        )
        # Validate computed layout
        cd = CollisionDetector(canvas_w, canvas_h)
        cd.check_regions(self.layout.as_regions())

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def width(self) -> float:
        return self.layout.canvas_w

    @property
    def height(self) -> float:
        return self.layout.canvas_h

    # ── Layer builders ────────────────────────────────────────────────────────

    def _semiconductor_layer(self) -> Layer:
        layer = Layer(name="semiconductor", z_index=1)
        sl = self.layout
        JunctionBody(
            x=sl.p_box.x, y=sl.block_y,
            p_width=sl.p_box.width, n_width=sl.n_box.width,
            depletion_width=sl.dep_box.width,
            height=sl.block_height,
        ).build(layer)
        DepletionRegion(
            x=sl.dep_box.x, y=sl.block_y,
            width=sl.dep_box.width, height=sl.block_height,
        ).build(layer)
        DepletionIonGrid(
            dep_x=sl.dep_box.x, dep_width=sl.dep_box.width,
            dep_y=sl.block_y, dep_height=sl.block_height,
        ).build(layer)
        return layer

    def _carrier_layer(self) -> Layer:
        layer = Layer(name="carriers", z_index=3)
        sl = self.layout
        p = sl.p_box
        n = sl.n_box
        # Centre grids within their regions using a 30px margin
        margin = 30.0
        HoleGrid(
            x=p.x + margin, y=sl.block_y + margin,
            rows=3, cols=3, spacing_x=58, spacing_y=46,
            radius=8, show_arrows=True, arrow_length=18,
        ).build(layer)
        ElectronGrid(
            x=n.x + margin, y=sl.block_y + margin,
            rows=3, cols=3, spacing_x=60, spacing_y=46,
            radius=7, show_arrows=True, arrow_length=18,
        ).build(layer)
        return layer

    def _field_layer(self) -> Layer:
        layer = Layer(name="field", z_index=4)
        sl = self.layout
        dep = sl.dep_box
        y_e  = sl.block_y + sl.block_height * 0.35
        y_ei = sl.block_y + sl.block_height * 0.65

        # External field E: spans full semiconductor, points right
        layer.add(FieldArrow(
            id="e_external",
            position=(sl.p_box.x + 14, y_e),
            end=(sl.n_box.right - 14, y_e),
            head_size=6, label="E", label_side="above", label_offset=11,
            style=Style(stroke="#222222", stroke_width=1.1,
                        font_size=10, fill="#222222",
                        font_family="Arial", text_anchor="middle"),
        ))
        # Internal field Ei: spans depletion, points left
        layer.add(FieldArrow(
            id="e_internal",
            position=(dep.right - 10, y_ei),
            end=(dep.x + 10, y_ei),
            head_size=6, label="Ei", label_side="above", label_offset=11,
            style=Style(stroke="#222222", stroke_width=1.1,
                        font_size=10, fill="#222222",
                        font_family="Arial", text_anchor="middle"),
        ))
        return layer

    def _circuit_layer(self) -> Layer:
        layer = Layer(name="circuit", z_index=2)
        c = self.circ
        wire_style = Style(stroke="#000000", stroke_width=1.4)
        cy = c.circuit_y

        layer.add(WirePath(
            id="wire_left_arm", position=(0, 0),
            waypoints=[(x, y) for x, y in c.wire_left_arm],
            style=wire_style,
        ))
        layer.add(SwitchSymbol(
            id="switch_k",
            position=(c.switch_x, cy),
            length=c.switch_length, open=False, label="K",
            style=wire_style,
        ))
        layer.add(WirePath(
            id="wire_to_battery", position=(0, 0),
            waypoints=[(x, y) for x, y in c.wire_switch_to_battery],
            style=wire_style,
        ))
        layer.add(BatterySymbol(
            id="battery_e",
            position=(c.battery_x, cy),
            orientation="horizontal", positive_on="left", cells=c.battery_cells,
            style=wire_style,
        ))
        layer.add(WirePath(
            id="wire_to_resistor", position=(0, 0),
            waypoints=[(x, y) for x, y in c.wire_battery_to_resistor],
            style=wire_style,
        ))
        layer.add(ResistorSymbol(
            id="resistor_rh",
            position=(c.resistor_x, cy),
            length=c.resistor_length, label="Rh",
            style=wire_style,
        ))
        layer.add(WirePath(
            id="wire_right_arm", position=(0, 0),
            waypoints=[(x, y) for x, y in c.wire_right_arm],
            style=wire_style,
        ))
        return layer

    def _label_layer(self, title: str = "PN Junction") -> Layer:
        layer = Layer(name="labels", z_index=5)
        sl = self.layout
        dep = sl.dep_box
        p = sl.p_box
        n = sl.n_box
        label_y = sl.block_y - 13

        RegionLabel("label_p",  p.cx,   label_y, "p",  18).build(layer)
        RegionLabel("label_n",  n.cx,   label_y, "n",  18).build(layer)
        layer.add(Text(id="label_dep", position=(dep.cx, label_y), content="Depl.",
                       style=Style(fill="#444444", stroke="none", font_size=9, text_anchor="middle")))
        layer.add(Text(id="label_holes", position=(p.cx, sl.bottom_y + 14), content="Holes",
                       style=Style(fill="#000000", stroke="none", font_size=11, text_anchor="middle")))
        layer.add(Text(id="label_electrons", position=(n.cx, sl.bottom_y + 14), content="Electrons",
                       style=Style(fill="#000000", stroke="none", font_size=11, text_anchor="middle")))
        layer.add(Text(id="title", position=(sl.canvas_w / 2, 30), content=title,
                       style=Style(fill="#000000", stroke="none",
                                   font_size=16, font_weight="bold", text_anchor="middle")))
        layer.add(Text(id="caption",
                       position=(sl.canvas_w / 2, sl.canvas_h - 18),
                       content="Fig. 14.15  Forward biasing of a p-n junction.",
                       style=Style(fill="#333333", stroke="none", font_size=10, text_anchor="middle")))
        return layer

    # ── Public scene constructors ─────────────────────────────────────────────

    def build_scene(self, title: str = "PN Junction") -> Scene:
        """Bare PN junction — semiconductor body + labels only."""
        scene = Scene(title=title, width=self.width, height=self.height)
        scene.add_layer(self._semiconductor_layer())
        scene.add_layer(self._label_layer(title))
        return scene

    def build_forward_bias_scene(self) -> Scene:
        """Complete forward-biased PN junction (programmatic path)."""
        title = "Forward Biased PN Junction"
        scene = Scene(title=title, width=self.width, height=self.height, background="#FFFFFF")
        scene.add_layer(self._semiconductor_layer())
        scene.add_layer(self._carrier_layer())
        scene.add_layer(self._field_layer())
        scene.add_layer(self._circuit_layer())
        scene.add_layer(self._label_layer(title))
        return scene
