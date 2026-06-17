from pathlib import Path

import schemdraw
import schemdraw.elements as elm


class CircuitRenderer:

    def render(self, blueprint):

        circuit_type = blueprint["circuit_type"]

        if circuit_type in {
            "simple_series",
            "series_resistors",
            "three_resistor_series",
            "ammeter_series",
            "cell_key_bulb"
        }:
            return self._render_series(blueprint)

        elif circuit_type in {
            "parallel_resistors",
            "three_parallel",
            "voltmeter_parallel"
        }:
            return self._render_parallel(blueprint)

        elif circuit_type == "wheatstone_bridge":
            return self._render_wheatstone()

        elif circuit_type == "meter_bridge":
            return self._render_meter_bridge()

        raise ValueError(
            f"Unsupported circuit type: {circuit_type}"
        )

    # --------------------------------------------------
    # SERIES
    # --------------------------------------------------

    def _render_series(self, blueprint):

        d = schemdraw.Drawing()

        for component in blueprint["components"]:

            ctype = component["type"]

            if ctype == "battery":
                d += elm.Battery().label("Battery")

            elif ctype == "cell":
                d += elm.Cell().label("Cell")

            elif ctype == "key":
                d += elm.Switch().label("K")

            elif ctype == "bulb":
                d += elm.Lamp().label("L")

            elif ctype == "ammeter":
                d += elm.MeterA().label("A")

            elif ctype == "resistor":

                value = component.get(
                    "resistance",
                    ""
                )

                d += elm.Resistor().label(
                    f"{value}Ω"
                )

        d += elm.Line().down()
        d += elm.Line().left(
            d.unit * len(
                blueprint["components"]
            )
        )
        d += elm.Line().up()

        return d

    # --------------------------------------------------
    # PARALLEL
    # --------------------------------------------------

    def _render_parallel(self, blueprint):

        d = schemdraw.Drawing()

        d += elm.Battery().up()

        d.push()

        d += elm.Line().right()

        d.push()

        d += elm.Resistor().down().label("R1")
        d += elm.Line().left()

        d.pop()

        d += elm.Line().right(2)

        d += elm.Resistor().down().label("R2")
        d += elm.Line().left(2)

        d.pop()

        return d

    # --------------------------------------------------
    # WHEATSTONE
    # --------------------------------------------------

    def _render_wheatstone(self):

        d = schemdraw.Drawing()

        d += elm.Resistor().right().label("P")
        d += elm.Resistor().down().label("Q")
        d += elm.Resistor().left().label("R")
        d += elm.Resistor().up().label("S")

        return d

    # --------------------------------------------------
    # METER BRIDGE
    # --------------------------------------------------

    def _render_meter_bridge(self):

        d = schemdraw.Drawing()

        d += elm.Line().right(6).label(
            "Meter Wire"
        )

        return d

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    def render_to_file(
        self,
        blueprint,
        output_file
    ):

        drawing = self.render(
            blueprint
        )

        drawing.save(output_file)

        return output_file


# ------------------------------------------------------
# TEST RUNNER
# ------------------------------------------------------

if __name__ == "__main__":

    import json

    with open(
        "circuit_blueprints.json",
        "r",
        encoding="utf-8"
    ) as f:

        blueprints = json.load(f)

    renderer = CircuitRenderer()

    output_dir = Path("output")
    output_dir.mkdir(
        exist_ok=True
    )

    print(
        "\nCIRCUIT RENDER TEST\n"
    )

    for bp in blueprints:

        try:

            file_path = (
                output_dir /
                f"{bp['question_id']}.svg"
            )

            renderer.render_to_file(
                bp,
                str(file_path)
            )

            print(
                bp["question_id"],
                "->",
                file_path
            )

        except Exception as e:

            print(
                bp["question_id"],
                "FAILED",
                e
            )
