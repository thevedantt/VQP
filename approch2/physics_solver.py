class PhysicsSolver:

    def solve_convex_lens(
        self,
        scenario
    ):

        solutions = {

            "between_f_and_2f": {

                "image_x": 820,

                "image_height": 180,

                "image_orientation":
                "inverted"
            },

            "beyond_2f": {

                "image_x": 650,

                "image_height": 60,

                "image_orientation":
                "inverted"
            },

            "at_2f": {

                "image_x": 700,

                "image_height": 100,

                "image_orientation":
                "inverted"
            },

            "inside_f": {

                "image_x": 250,

                "image_height": 180,

                "image_orientation":
                "erect"
            }
        }

        return solutions.get(
            scenario,
            {}
        )