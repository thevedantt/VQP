from renderers.ray_renderer import RayRenderer


class SVGRenderer:

    def __init__(self):

        self.ray_renderer = RayRenderer()

    def render(self, blueprint):

        if blueprint["renderer_type"] == "ray":

            return self.ray_renderer.render_convex_lens(
                blueprint
            )

        return "<svg></svg>"