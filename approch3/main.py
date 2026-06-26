"""
VisualQ Diagram Engine — entry point.
Compiles the forward-biased PN junction template to SVG (and optionally PNG).

The active theme (NCERTTheme by default) drives all styling decisions.
To switch themes: pass a different theme class to DiagramCompiler().
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

from visualq_diagram_engine.core.compiler import DiagramCompiler
from visualq_diagram_engine.core.export import Exporter
from visualq_diagram_engine.theme.ncert_theme import NCERTTheme


def main() -> None:
    config = {
        "output_dir": os.getenv("OUTPUT_DIR", "output"),
        "export_png": os.getenv("EXPORT_PNG", "true").lower() == "true",
        "svg_width": int(os.getenv("SVG_WIDTH", "1200")),
        "svg_height": int(os.getenv("SVG_HEIGHT", "800")),
        "debug": DEBUG,
        "templates_dir": str(Path(__file__).parent / "visualq_diagram_engine" / "templates"),
    }

    compiler = DiagramCompiler(config, theme=NCERTTheme)
    exporter = Exporter()

    output_dir = Path(config["output_dir"])
    exporter.ensure_output_dir(str(output_dir))

    logging.info("Compiling template: pn_forward")
    scene, canvas = compiler.compile("pn_forward")
    logging.info(
        "Scene '%s' built — %d layers, %d total objects",
        scene.title,
        len(scene.layers),
        len(scene.all_objects()),
    )

    svg_path = str(output_dir / "pn_forward_bias.svg")
    exporter.export_svg(canvas, svg_path)

    if config["export_png"]:
        png_path = str(output_dir / "pn_forward_bias.png")
        exporter.export_png(svg_path, png_path)

    logging.info("Done.")
    print(f"\nOutput written to: {output_dir.resolve()}")
    print(f"  SVG: {svg_path}")
    if config["export_png"]:
        print(f"  PNG: {output_dir / 'pn_forward_bias.png'} (requires cairosvg)")


if __name__ == "__main__":
    main()
