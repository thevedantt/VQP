"""DiagramCompiler — orchestrates the full compile pipeline."""

import logging
from pathlib import Path

from visualq_diagram_engine.compiler.template_loader import TemplateLoader
from visualq_diagram_engine.compiler.scene_builder import SceneBuilder
from visualq_diagram_engine.compiler.layout_resolver import LayoutResolver
from visualq_diagram_engine.core.validator import DiagramValidator
from visualq_diagram_engine.core.renderer import SVGRenderer
from visualq_diagram_engine.core.scene import Scene
from visualq_diagram_engine.core.svg_canvas import SVGCanvas
from visualq_diagram_engine.theme.base_theme import BaseTheme

logger = logging.getLogger(__name__)


class DiagramCompiler:
    def __init__(self, config: dict, theme: type[BaseTheme] | None = None):
        self._config = config
        # Activate theme: sets global active theme and passes it to the resolver
        if theme is None:
            from visualq_diagram_engine.theme.ncert_theme import NCERTTheme
            theme = NCERTTheme
        self._theme = theme

        templates_dir = config.get(
            "templates_dir",
            str(Path(__file__).parent.parent / "templates"),
        )
        from visualq_diagram_engine.theme import set_theme
        set_theme(theme)

        self._loader    = TemplateLoader(templates_dir)
        self._resolver  = LayoutResolver(theme=theme)
        self._builder   = SceneBuilder()
        self._validator = DiagramValidator()
        self._renderer  = SVGRenderer(config)

    def compile(self, template_name: str) -> tuple[Scene, SVGCanvas]:
        """Load template, resolve layout, validate, build scene, render."""
        logger.info("Loading template: %s", template_name)
        spec = self._loader.load(template_name)
        return self.compile_from_spec(spec)

    def compile_from_spec(self, spec: dict) -> tuple[Scene, SVGCanvas]:
        """Compile directly from a spec dict (layout section resolved first)."""
        spec = self._resolver.resolve(spec)
        self._validator.validate_spec(spec)
        scene = self._builder.build(spec)
        canvas = self._renderer.render(scene)
        return scene, canvas
