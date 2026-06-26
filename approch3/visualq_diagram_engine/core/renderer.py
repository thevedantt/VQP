"""SVG renderer — converts a Scene into an SVGCanvas."""

import logging
from visualq_diagram_engine.core.scene import Scene
from visualq_diagram_engine.core.svg_canvas import SVGCanvas

logger = logging.getLogger(__name__)


class SVGRenderer:
    def __init__(self, config: dict):
        self._width = config.get("svg_width", 800)
        self._height = config.get("svg_height", 600)
        self._background = config.get("background", "#FFFFFF")

    def render(self, scene: Scene) -> SVGCanvas:
        """Render the scene and return a populated SVGCanvas."""
        width = scene.width or self._width
        height = scene.height or self._height
        background = scene.background or self._background

        canvas = SVGCanvas(width=width, height=height, background=background)

        # Define standard arrowhead markers used by Arrow primitives
        canvas.define_arrowhead_marker("arrowhead-black", "#000000", size=8)
        canvas.define_arrowhead_marker("arrowhead-red", "#CC0000", size=8)
        canvas.define_arrowhead_marker("arrowhead-blue", "#0000CC", size=8)
        canvas.define_arrowhead_marker("arrowhead-gray", "#666666", size=7)

        objects = scene.all_objects()
        logger.debug("Rendering %d objects in scene '%s'", len(objects), scene.title)

        for node in objects:
            try:
                node.render(canvas)
            except Exception as exc:
                logger.warning("Failed to render node '%s': %s", node.id, exc)

        logger.info("Scene '%s' rendered (%dx%d)", scene.title, int(width), int(height))
        return canvas
