from ray_math import RayMath


class PhysicsSolver:
    """Provides solved optical parameters for a convex lens given object data.

    All computation delegates to RayMath.  This class owns the focal-length
    constant and exposes results that downstream code (the renderer) can
    consume without needing to know the sign conventions.
    """

    def __init__(self, focal_length: float = 100.0):
        self.ray_math = RayMath(focal_length)

    def solve_convex_lens(
        self, lens_x: float, object_x: float, object_height: float, scenario: str
    ) -> dict:
        """Solve the lens equation for the given object.

        Returns a flat dict containing every parameter the renderer needs:

            u              object distance (lens_x − object_x)  [px]
            f              focal length                         [px]
            v              image distance                       [px]
            magnification  linear magnification (v / u)
            orientation    "inverted" | "erect"
            image_type     "real" | "virtual"
            image_x        world x-coordinate of image          [px]
            image_height   height of the image                  [px]

        The ``scenario`` argument is *not* used in computation; it is
        carried along for labelling only.
        """
        u = object_x - lens_x
        v, m = self.ray_math.solve_lens(u)

        orientation = "erect" if m > 0 else "inverted"
        image_type = "virtual" if v < 0 else "real"

        image_x = self.ray_math.calculate_image_position(lens_x, v)
        image_height = self.ray_math.calculate_image_height(object_height, m)

        return {
            "u": u,
            "f": self.ray_math.f,
            "v": v,
            "magnification": m,
            "orientation": orientation,
            "image_type": image_type,
            "image_x": image_x,
            "image_height": image_height,
        }
