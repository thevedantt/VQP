"""Tests for SVGRenderer and SVGCanvas."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from visualq_diagram_engine.core.scene import Scene, Layer
from visualq_diagram_engine.core.renderer import SVGRenderer
from visualq_diagram_engine.core.svg_canvas import SVGCanvas
from visualq_diagram_engine.primitives.rectangle import Rectangle
from visualq_diagram_engine.primitives.styles import Style


def _make_minimal_scene() -> Scene:
    scene = Scene(title="Test Scene", width=400, height=300, background="#FFFFFF")
    layer = Layer(name="test", z_index=0)
    layer.add(Rectangle(
        id="rect1",
        position=(10, 10),
        width=100,
        height=60,
        style=Style(fill="#FF0000", stroke="#000000"),
    ))
    scene.add_layer(layer)
    return scene


def test_renderer_creates_canvas():
    renderer = SVGRenderer(config={"svg_width": 400, "svg_height": 300})
    scene = _make_minimal_scene()
    canvas = renderer.render(scene)
    assert isinstance(canvas, SVGCanvas), "render() must return an SVGCanvas"


def test_svg_canvas_save(tmp_path):
    renderer = SVGRenderer(config={"svg_width": 400, "svg_height": 300})
    scene = _make_minimal_scene()
    canvas = renderer.render(scene)
    out_path = str(tmp_path / "test_output.svg")
    canvas.save(out_path)

    assert Path(out_path).exists(), "SVG file was not created"
    content = Path(out_path).read_text(encoding="utf-8")
    assert "<svg" in content, "SVG file does not contain <svg tag"


def test_renderer_respects_scene_dimensions():
    renderer = SVGRenderer(config={})
    scene = Scene(title="Sized", width=600, height=400)
    canvas = renderer.render(scene)
    drawing = canvas.get_drawing()
    # svgwrite stores size as strings like "600px"
    assert "600" in str(drawing.attribs.get("width", ""))
    assert "400" in str(drawing.attribs.get("height", ""))
