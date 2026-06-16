import json


with open(
    "data/generated_schemas.json",
    "r",
    encoding="utf-8"
) as f:

    schemas = json.load(f)


blueprints = []


for schema in schemas:

    blueprint = {

        "question_id":
        schema["question_id"],

        "renderer_type":
        "ray",

        "principal_axis": True,

        "lens": {
            "x": 400
        },

        "focal_points": {
            "F1": 320,
            "2F1": 220,
            "F2": 480,
            "2F2": 580
        },

        "object": {
            "x": 300,
            "height": 80
        },

        "image": {
            "x": 620,
            "height": 120
        },

        "rays": [
            "parallel_ray",
            "optical_center_ray"
        ]
    }

    blueprints.append(blueprint)


with open(
    "data/physics_blueprints.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        blueprints,
        f,
        indent=2
    )

print("Blueprints Generated")