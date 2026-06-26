"""DiagramParser — thin facade over TemplateLoader + YAMLParser."""

import logging
from pathlib import Path

from visualq_diagram_engine.compiler.template_loader import TemplateLoader
from visualq_diagram_engine.compiler.yaml_parser import YAMLParser

logger = logging.getLogger(__name__)


class DiagramParser:
    def __init__(self, templates_dir: str):
        self._loader = TemplateLoader(templates_dir)
        self._parser = YAMLParser()

    def parse_template(self, name: str) -> dict:
        """Load a named template and return its parsed spec dict."""
        return self._loader.load(name)

    def parse_file(self, path: str) -> dict:
        """Parse an arbitrary YAML file."""
        return self._parser.load(path)
