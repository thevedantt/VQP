from physics_solver import PhysicsSolver
from ray_rules import RULES


class RayRenderer:

    def __init__(self):
        self.solver = PhysicsSolver()

    def render_convex_lens(self, blueprint):

        axis_y = blueprint["principal_axis"]["y"]

        lens_x = blueprint["lens"]["x"]

        f1 = blueprint["focal_points"]["F1"]
        f2 = blueprint["focal_points"]["F2"]

        two_f1 = blueprint["focal_points"]["2F1"]
        two_f2 = blueprint["focal_points"]["2F2"]

        object_x = blueprint["object"]["x"]
        object_height = blueprint["object"]["height"]

        scenario = blueprint["scenario"]

        solution = self.solver.solve_convex_lens(
            scenario
        )

        rule = RULES.get(
            scenario
        )

        image_x = solution["image_x"]

        image_height = solution["image_height"]

        orientation = solution[
            "image_orientation"
        ]

        ray_mode = rule[
            "ray_mode"
        ]

        object_top_y = (
            axis_y - object_height
        )

        if orientation == "inverted":

            image_top_y = (
                axis_y + image_height
            )

        else:

            image_top_y = (
                axis_y - image_height
            )

        svg = f"""
<svg xmlns="http://www.w3.org/2000/svg"
     width="1200"
     height="700">

<!-- Principal Axis -->

<line
    x1="50"
    y1="{axis_y}"
    x2="1150"
    y2="{axis_y}"
    stroke="black"
    stroke-width="2"/>

<!-- Convex Lens -->

<ellipse
    cx="{lens_x}"
    cy="{axis_y}"
    rx="15"
    ry="160"
    fill="none"
    stroke="blue"
    stroke-width="3"/>

<!-- Lens Label -->

<text
    x="{lens_x-45}"
    y="{axis_y-180}">
    Convex Lens
</text>

<!-- Focal Points -->

<circle cx="{f1}" cy="{axis_y}" r="4" fill="black"/>
<circle cx="{f2}" cy="{axis_y}" r="4" fill="black"/>

<circle cx="{two_f1}" cy="{axis_y}" r="4" fill="black"/>
<circle cx="{two_f2}" cy="{axis_y}" r="4" fill="black"/>

<text x="{f1-10}" y="{axis_y+25}">F1</text>
<text x="{f2-10}" y="{axis_y+25}">F2</text>

<text x="{two_f1-15}" y="{axis_y+25}">2F1</text>
<text x="{two_f2-15}" y="{axis_y+25}">2F2</text>

<!-- Object -->

<line
    x1="{object_x}"
    y1="{axis_y}"
    x2="{object_x}"
    y2="{object_top_y}"
    stroke="black"
    stroke-width="3"/>

<polygon
    points="
    {object_x-7},{object_top_y+10}
    {object_x+7},{object_top_y+10}
    {object_x},{object_top_y-10}
    "
    fill="black"/>

<text
    x="{object_x-25}"
    y="{object_top_y-20}">
    Object
</text>

<!-- Image -->

<line
    x1="{image_x}"
    y1="{axis_y}"
    x2="{image_x}"
    y2="{image_top_y}"
    stroke="black"
    stroke-width="3"/>
"""

        if orientation == "inverted":

            svg += f"""
<polygon
    points="
    {image_x-7},{image_top_y-10}
    {image_x+7},{image_top_y-10}
    {image_x},{image_top_y+10}
    "
    fill="black"/>
"""

        else:

            svg += f"""
<polygon
    points="
    {image_x-7},{image_top_y+10}
    {image_x+7},{image_top_y+10}
    {image_x},{image_top_y-10}
    "
    fill="black"/>
"""

        svg += f"""
<text
    x="{image_x-20}"
    y="{image_top_y+35}">
    Image
</text>
"""

        if ray_mode == "real":

            svg += f"""

<!-- Parallel Ray -->

<line
    x1="{object_x}"
    y1="{object_top_y}"
    x2="{lens_x}"
    y2="{object_top_y}"
    stroke="red"
    stroke-width="2"/>

<line
    x1="{lens_x}"
    y1="{object_top_y}"
    x2="{image_x}"
    y2="{image_top_y}"
    stroke="red"
    stroke-width="2"/>

<!-- Optical Center Ray -->

<line
    x1="{object_x}"
    y1="{object_top_y}"
    x2="{image_x}"
    y2="{image_top_y}"
    stroke="green"
    stroke-width="2"/>
"""

        else:

            svg += f"""

<!-- Parallel Ray -->

<line
    x1="{object_x}"
    y1="{object_top_y}"
    x2="{lens_x}"
    y2="{object_top_y}"
    stroke="red"
    stroke-width="2"/>

<line
    x1="{lens_x}"
    y1="{object_top_y}"
    x2="1100"
    y2="120"
    stroke="red"
    stroke-width="2"/>

<!-- Back Extension -->

<line
    x1="{lens_x}"
    y1="{object_top_y}"
    x2="{image_x}"
    y2="{image_top_y}"
    stroke="red"
    stroke-dasharray="6,6"
    stroke-width="2"/>

<!-- Optical Center Ray -->

<line
    x1="{object_x}"
    y1="{object_top_y}"
    x2="1100"
    y2="500"
    stroke="green"
    stroke-width="2"/>

<!-- Back Extension -->

<line
    x1="{object_x}"
    y1="{object_top_y}"
    x2="{image_x}"
    y2="{image_top_y}"
    stroke="green"
    stroke-dasharray="6,6"
    stroke-width="2"/>
"""

        svg += """

</svg>
"""

        return svg