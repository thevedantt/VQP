"""Template loader — resolves template names to YAML dicts."""

import logging
from pathlib import Path

from visualq_diagram_engine.compiler.yaml_parser import YAMLParser, ParseError

logger = logging.getLogger(__name__)


class TemplateLoader:
    def __init__(self, templates_dir: str):
        self._dir = Path(templates_dir)
        self._parser = YAMLParser()

    def load(self, name: str) -> dict:
        """Load template by name (without .yaml extension)."""
        path = self._dir / f"{name}.yaml"
        logger.debug("Loading template '%s' from %s", name, path)
        return self._parser.load(str(path))
