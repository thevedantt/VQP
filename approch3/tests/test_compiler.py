"""Tests for DiagramCompiler and SceneBuilder."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from visualq_diagram_engine.core.compiler import DiagramCompiler
from visualq_diagram_engine.core.scene import Scene
from visualq_diagram_engine.core.svg_canvas import SVGCanvas
from visualq_diagram_engine.compiler.scene_builder import SceneBuilder

TEMPLATES_DIR = str(Path(__file__).parent.parent / "visualq_diagram_engine" / "templates")

CONFIG = {
    "svg_width": 800,
    "svg_height": 550,
    "templates_dir": TEMPLATES_DIR,
    "debug": False,
}


def test_compiler_builds_scene():
    compiler = DiagramCompiler(CONFIG)
    scene, canvas = compiler.compile("pn_forward")
    assert isinstance(scene, Scene), "compile() must return a Scene"
    assert isinstance(canvas, SVGCanvas), "compile() must return an SVGCanvas"
    assert len(scene.layers) > 0, "Scene must have at least one layer"


def test_scene_has_objects():
    compiler = DiagramCompiler(CONFIG)
    scene, _ = compiler.compile("pn_forward")
    all_objects = scene.all_objects()
    assert len(all_objects) > 10, f"Expected many objects in PN junction scene, got {len(all_objects)}"


def test_scene_builder_minimal():
    spec = {
        "scene": {"title": "Mini", "width": 200, "height": 100},
        "layers": [
            {
                "name": "base",
                "z_index": 0,
                "objects": [
                    {"type": "rectangle", "id": "r1", "x": 10, "y": 10, "width": 50, "height": 30,
                     "style": {"fill": "#AAAAAA"}},
                    {"type": "circle", "id": "c1", "x": 80, "y": 50, "radius": 20},
                    {"type": "text", "id": "t1", "x": 100, "y": 80, "content": "Hello"},
                ],
            }
        ],
    }
    builder = SceneBuilder()
    scene = builder.build(spec)
    assert scene.title == "Mini"
    assert len(scene.layers) == 1
    assert len(scene.layers[0].objects) == 3


def test_compiler_scene_title():
    compiler = DiagramCompiler(CONFIG)
    scene, _ = compiler.compile("pn_forward")
    assert "PN Junction" in scene.title or "Forward" in scene.title
