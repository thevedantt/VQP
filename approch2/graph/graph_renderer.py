import json
from pathlib import Path

import matplotlib.pyplot as plt


BLUEPRINT_FILE = (
    Path(__file__).parent /
    "graph_blueprints.json"
)

OUTPUT_DIR = (
    Path(__file__).parent /
    "output"
)

OUTPUT_DIR.mkdir(exist_ok=True)


plt.rcParams.update({
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "lines.linewidth": 2,
    "grid.alpha": 0.3,
    "figure.dpi": 100,
    "savefig.dpi": 100,
})


def _save(path):
    plt.tight_layout()
    plt.savefig(path, format="svg", bbox_inches="tight")
    plt.close()


def render_linear_graph(path):

    plt.figure(figsize=(6, 4))

    plt.plot([0, 10], [0, 10])

    plt.title("Linear Graph")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.grid(True)

    _save(path)


def render_distance_time(path):

    plt.figure(figsize=(6, 4))

    plt.plot([0, 2, 4, 6, 8], [0, 20, 40, 60, 80])

    plt.title("Distance-Time Graph")
    plt.xlabel("Time (s)")
    plt.ylabel("Distance (m)")
    plt.grid(True)

    _save(path)


def render_velocity_time(path):

    plt.figure(figsize=(6, 4))

    plt.plot([0, 2, 4, 6, 8], [0, 20, 40, 40, 40])

    plt.title("Velocity-Time Graph")
    plt.xlabel("Time (s)")
    plt.ylabel("Velocity (m/s)")
    plt.grid(True)

    _save(path)


def render_current_voltage(path):

    plt.figure(figsize=(6, 4))

    plt.plot([0, 1, 2, 3, 4], [0, 2, 4, 6, 8])

    plt.title("Current-Voltage Characteristics")
    plt.xlabel("Voltage (V)")
    plt.ylabel("Current (A)")
    plt.grid(True)

    _save(path)


def render_photoelectric(path):

    plt.figure(figsize=(6, 4))

    plt.plot([2, 3, 4, 5, 6], [0, 1, 2, 3, 4])

    plt.axvline(x=2, linestyle="--", color="#e74c3c", linewidth=1.5)

    plt.title("Photoelectric Effect")
    plt.xlabel("Frequency")
    plt.ylabel("Maximum Kinetic Energy")
    plt.grid(True)

    _save(path)


def render_semiconductor(path):

    plt.figure(figsize=(6, 4))

    x = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    y = [0, 0, 0.1, 0.5, 2, 5]

    plt.plot(x, y)

    plt.title("Semiconductor Characteristics")
    plt.xlabel("Voltage (V)")
    plt.ylabel("Current (mA)")
    plt.grid(True)

    _save(path)


def render_capacitor_charging(path):

    plt.figure(figsize=(6, 4))

    x = [0, 1, 2, 3, 4, 5]
    y = [0, 0.63, 0.86, 0.95, 0.98, 1]

    plt.plot(x, y)

    plt.title("Capacitor Charging")
    plt.xlabel("Time (s)")
    plt.ylabel("Charge (Q/Q\u2080)")
    plt.grid(True)

    _save(path)


def render_capacitor_discharging(path):

    plt.figure(figsize=(6, 4))

    x = [0, 1, 2, 3, 4, 5]
    y = [1, 0.37, 0.14, 0.05, 0.02, 0]

    plt.plot(x, y)

    plt.title("Capacitor Discharging")
    plt.xlabel("Time (s)")
    plt.ylabel("Charge (Q/Q\u2080)")
    plt.grid(True)

    _save(path)


def render_graph(object_type, output_file):

    if object_type == "linear_graph":
        render_linear_graph(output_file)

    elif object_type == "distance_time":
        render_distance_time(output_file)

    elif object_type == "velocity_time":
        render_velocity_time(output_file)

    elif object_type == "current_voltage":
        render_current_voltage(output_file)

    elif object_type == "photoelectric":
        render_photoelectric(output_file)

    elif object_type == "semiconductor_characteristics":
        render_semiconductor(output_file)

    elif object_type == "capacitor_charging":
        render_capacitor_charging(output_file)

    elif object_type == "capacitor_discharging":
        render_capacitor_discharging(output_file)


def main():

    with open(
        BLUEPRINT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        blueprints = json.load(f)

    print()
    print("GRAPH RENDER REPORT")
    print("=" * 60)

    for bp in blueprints:

        output_file = (
            OUTPUT_DIR /
            f"{bp['question_id']}.svg"
        )

        render_graph(
            bp["object_type"],
            output_file
        )

        print()
        print(bp["question_id"])
        print(output_file)

    print()


if __name__ == "__main__":
    main()
