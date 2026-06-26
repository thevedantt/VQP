"""SVG and PNG exporter."""

import logging
import os
from pathlib import Path

from visualq_diagram_engine.core.svg_canvas import SVGCanvas

logger = logging.getLogger(__name__)


class Exporter:
    def ensure_output_dir(self, path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)
        logger.debug("Output directory ready: %s", path)

    def export_svg(self, canvas: SVGCanvas, path: str) -> None:
        self.ensure_output_dir(str(Path(path).parent))
        canvas.save(path)
        logger.info("SVG exported: %s", path)

    def export_png(self, svg_path: str, png_path: str, scale: float = 2.0) -> None:
        try:
            import cairosvg
            cairosvg.svg2png(
                url=svg_path,
                write_to=png_path,
                scale=scale,
            )
            logger.info("PNG exported: %s", png_path)
        except ImportError:
            logger.warning(
                "cairosvg is not installed or Cairo system library is missing. "
                "PNG export skipped. Install cairosvg and GTK/Cairo to enable PNG export."
            )
        except Exception as exc:
            logger.warning("PNG export failed: %s", exc)
