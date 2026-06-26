"""
FBDBuilder — Free Body Diagram builder.

Phase 2 scope:
- Accept a body description (shape, mass, position)
- Accept a list of forces (name, magnitude, direction_degrees, point_of_application)
- Render the body as a rectangle/circle primitive
- Render each force as a scaled Arrow with label
- Auto-scale arrow lengths proportional to magnitude
- Draw reference axes (x, y) with optional angle
- Support inclined planes with angled coordinate systems
- Add a net force resultant arrow (optional)

Force types to support:
  Weight (W = mg, downward)
  Normal force (perpendicular to surface)
  Friction (along surface, opposing motion)
  Tension (along string/rope)
  Applied force (arbitrary direction)
  Buoyancy (upward in fluid)
"""

from dataclasses import dataclass, field
from visualq_diagram_engine.core.scene import Scene


@dataclass
class Force:
    name: str
    magnitude: float
    direction_degrees: float
    color: str = "#CC0000"


@dataclass
class Body:
    shape: str = "rectangle"
    width: float = 60
    height: float = 40
    label: str = "m"


class FBDBuilder:
    """Free Body Diagram builder (Phase 2)."""

    def __init__(self, body: Body = None):
        self.body = body or Body()
        self.forces: list[Force] = []

    def add_force(self, force: Force) -> "FBDBuilder":
        self.forces.append(force)
        return self

    def build(self) -> Scene:
        """Build the FBD scene. Not yet implemented."""
        raise NotImplementedError("FBDBuilder is planned for Phase 2")
