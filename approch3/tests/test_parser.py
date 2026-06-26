"""Tests for YAML parser and template loader."""

import os
import sys
from pathlib import Path

# Ensure the project root is on the path when running tests directly
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from visualq_diagram_engine.compiler.yaml_parser import YAMLParser, ParseError
from visualq_diagram_engine.compiler.template_loader import TemplateLoader

TEMPLATES_DIR = str(Path(__file__).parent.parent / "visualq_diagram_engine" / "templates")


def test_parser_loads_yaml():
    parser = YAMLParser()
    path = str(Path(TEMPLATES_DIR) / "pn_forward.yaml")
    data = parser.load(path)
    assert isinstance(data, dict), "Expected a dict from YAML load"
    assert "scene" in data, "Expected 'scene' key in loaded YAML"


def test_parser_raises_on_missing_file():
    parser = YAMLParser()
    with pytest.raises(ParseError):
        parser.load("/nonexistent/path/missing.yaml")


def test_template_loader():
    loader = TemplateLoader(TEMPLATES_DIR)
    data = loader.load("pn_forward")
    assert "diagram" in data, "Expected 'diagram' key"
    assert "Junction" in data["diagram"]["title"]


def test_parse_style():
    parser = YAMLParser()
    style = parser.parse_style({"fill": "#FF0000", "stroke_width": 3.0})
    assert style.fill == "#FF0000"
    assert style.stroke_width == 3.0


def test_parse_position():
    parser = YAMLParser()
    pos = parser.parse_position({"x": 100, "y": 200})
    assert pos == (100.0, 200.0)
