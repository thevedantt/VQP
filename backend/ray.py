from manim import *

class ConvexLensRayDiagram(Scene):
    def construct(self):
        # Principal axis
        axis = Line(LEFT * 6, RIGHT * 6)
        self.add(axis)

        # Convex lens
        lens = DoubleArrow(
            UP * 2,
            DOWN * 2,
            buff=0,
            tip_length=0.15
        ).rotate(PI / 2)
        self.add(lens)

        # Focal points and 2F points
        F1 = Dot(LEFT * 2)
        F2 = Dot(RIGHT * 2)
        F1_label = Text("F", font_size=24).next_to(F1, DOWN)
        F2_label = Text("F", font_size=24).next_to(F2, DOWN)

        twoF1 = Dot(LEFT * 4)
        twoF2 = Dot(RIGHT * 4)
        twoF1_label = Text("2F", font_size=24).next_to(twoF1, DOWN)
        twoF2_label = Text("2F", font_size=24).next_to(twoF2, DOWN)

        self.add(
            F1, F2, twoF1, twoF2,
            F1_label, F2_label,
            twoF1_label, twoF2_label
        )

        # Object between F and 2F
        object_arrow = Arrow(
            start=LEFT * 3 + DOWN * 0.1,
            end=LEFT * 3 + UP * 1.5,
            buff=0,
            color=BLUE
        )

        object_label = Text("Object", font_size=24).next_to(
            object_arrow, LEFT
        )

        self.add(object_arrow, object_label)

        # Image beyond 2F (magnified, inverted)
        image_arrow = Arrow(
            start=RIGHT * 6 + UP * 0.1,
            end=RIGHT * 6 + DOWN * 3,
            buff=0,
            color=GREEN
        )

        image_label = Text("Image", font_size=24).next_to(
            image_arrow, RIGHT
        )

        self.add(image_arrow, image_label)

        # Ray 1: parallel to axis then through focus
        ray1_incident = Line(
            object_arrow.get_top(),
            [0, object_arrow.get_top()[1], 0],
            color=YELLOW
        )

        ray1_refracted = Line(
            [0, object_arrow.get_top()[1], 0],
            image_arrow.get_bottom(),
            color=YELLOW
        )

        # Ray 2: through optical center
        ray2 = Line(
            object_arrow.get_top(),
            image_arrow.get_bottom(),
            color=RED
        )

        self.play(Create(ray1_incident))
        self.play(Create(ray1_refracted))
        self.play(Create(ray2))
        self.wait()