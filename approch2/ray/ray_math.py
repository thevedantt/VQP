import math


class RayMath:
    """Physics formula calculations for ray diagrams using the Cartesian sign convention.

    Sign convention:
      - All distances measured from the optical centre of the lens.
      - Distances in the direction of incident light (left to right) are positive.
      - Distances opposite the direction of incident light are negative.
      - Object distance u is always negative (object is to the left of the lens).
      - Focal length f of a convex lens is positive.

    Lens formula:  1/f = 1/v - 1/u   ->   1/v = 1/f + 1/u
    Magnification: m = v / u
    Image height:  h' = |m| * h
    """

    def __init__(self, focal_length: float):
        if focal_length <= 0:
            raise ValueError("Focal length must be positive for a convex lens.")
        self.f = focal_length

    # ------------------------------------------------------------------ #
    #  Core lens formula
    # ------------------------------------------------------------------ #

    def solve_lens(self, u: float) -> tuple[float, float]:
        """Apply the lens formula to find image distance and magnification.

        Args:
            u: Object distance from optical centre (negative per convention).

        Returns:
            (v, m) where:
              v: image distance from optical centre.
                 positive  -> real image on opposite side (right of lens).
                 negative  -> virtual image on same side (left of lens).
              m: magnification = v / u.
                 negative  -> inverted image.
                 positive  -> erect image.
        """
        if u == 0:
            return (0.0, 0.0)
        if u == -self.f:
            return (float("inf"), float("inf"))

        v = 1.0 / (1.0 / self.f + 1.0 / u)
        m = v / u
        return (v, m)

    # ------------------------------------------------------------------ #
    #  Explicit calculation methods
    # ------------------------------------------------------------------ #

    def calculate_image_distance(self, u: float) -> float:
        """Return image distance v for a given object distance u."""
        v, _ = self.solve_lens(u)
        return v

    def calculate_magnification(self, v: float, u: float) -> float:
        """Return linear magnification m = v / u."""
        if u == 0:
            return 0.0
        return v / u

    def calculate_image_height(self, object_height: float, magnification: float) -> float:
        """Return absolute image height in pixels."""
        return abs(magnification) * object_height

    def calculate_image_position(self, lens_x: float, v: float) -> float:
        """Return the x-coordinate of the image on the canvas."""
        return lens_x + v

    # ------------------------------------------------------------------ #
    #  Convenience: image properties from object parameters
    # ------------------------------------------------------------------ #

    def image_properties(self, u: float) -> dict:
        """Return a complete description of the image for a given object distance.

        Returns dict with keys:
            v, magnification, image_type, orientation, relative_size.
        """
        v, m = self.solve_lens(u)

        if v == float("inf"):
            return {
                "v": v,
                "magnification": float("inf"),
                "image_type": "real",
                "orientation": "inverted",
                "relative_size": "highly_magnified",
            }

        image_type = "virtual" if v < 0 else "real"
        orientation = "erect" if m > 0 else "inverted"
        abs_m = abs(m)

        if abs_m > 1.01:
            relative_size = "magnified"
        elif abs_m < 0.99:
            relative_size = "diminished"
        else:
            relative_size = "same_size"

        return {
            "v": v,
            "magnification": m,
            "image_type": image_type,
            "orientation": orientation,
            "relative_size": relative_size,
        }

    def image_world_coords(
        self, lens_x: float, object_x: float, object_height: float
    ) -> dict:
        """Compute image position and size in world (SVG) coordinates.

        Args:
            lens_x: x-coordinate of the optical centre (lens centre).
            object_x: x-coordinate of the object base (on principal axis).
            object_height: height of the object in SVG pixels.

        Returns:
            dict with keys: image_x, image_height, orientation, v, m.
        """
        u = object_x - lens_x
        v, m = self.solve_lens(u)
        image_x = self.calculate_image_position(lens_x, v)
        image_height = self.calculate_image_height(object_height, m)
        orientation = "erect" if m > 0 else "inverted"

        return {
            "image_x": image_x,
            "image_height": image_height,
            "orientation": orientation,
            "v": v,
            "m": m,
        }

    # ------------------------------------------------------------------ #
    #  Focal point helpers
    # ------------------------------------------------------------------ #

    def focal_points(self, lens_x: float) -> dict[str, float]:
        """Return x-coordinates of F1, F2, 2F1, 2F2."""
        return {
            "F1": lens_x - self.f,
            "F2": lens_x + self.f,
            "2F1": lens_x - 2 * self.f,
            "2F2": lens_x + 2 * self.f,
        }

    def describe_scenario(self, u: float) -> str:
        """Classify the object position into a named scenario."""
        abs_u = abs(u)
        if abs_u > 2 * self.f:
            return "beyond_2f"
        if abs(abs_u - 2 * self.f) < 0.001:
            return "at_2f"
        if abs_u > self.f:
            return "between_f_and_2f"
        if abs(abs_u - self.f) < 0.001:
            return "at_f"
        if u < 0:
            return "inside_f"
        return "unknown"
