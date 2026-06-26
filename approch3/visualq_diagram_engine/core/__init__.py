"""
Core rendering pipeline.
Import individual modules directly to avoid circular imports, e.g.:
    from visualq_diagram_engine.core.compiler import DiagramCompiler
"""

__all__ = [
    "Scene", "Layer", "SceneNode",
    "SVGCanvas", "SVGRenderer",
    "DiagramCompiler", "Exporter",
    "DiagramValidator", "ValidationError",
]
