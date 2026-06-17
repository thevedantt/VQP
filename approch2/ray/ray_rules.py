RULES = {
    "beyond_2f": {
        "image_region": "between_f_and_2f",
        "ray_mode": "real",
        "num_rays": 3,
        "rays": [
            {
                "name": "parallel_ray",
                "label": "Ray 1",
                "description": "Parallel to axis -> refracts through F2",
                "draw_back_extension": False,
            },
            {
                "name": "optical_center_ray",
                "label": "Ray 2",
                "description": "Through optical centre -> undeviated",
                "draw_back_extension": False,
            },
            {
                "name": "focal_ray",
                "label": "Ray 3",
                "description": "Through F1 -> emerges parallel to axis",
                "draw_back_extension": False,
            },
        ],
    },
    "at_2f": {
        "image_region": "at_2f",
        "ray_mode": "real",
        "num_rays": 3,
        "rays": [
            {
                "name": "parallel_ray",
                "label": "Ray 1",
                "description": "Parallel to axis -> refracts through F2",
                "draw_back_extension": False,
            },
            {
                "name": "optical_center_ray",
                "label": "Ray 2",
                "description": "Through optical centre -> undeviated",
                "draw_back_extension": False,
            },
            {
                "name": "focal_ray",
                "label": "Ray 3",
                "description": "Through F1 -> emerges parallel to axis",
                "draw_back_extension": False,
            },
        ],
    },
    "between_f_and_2f": {
        "image_region": "beyond_2f",
        "ray_mode": "real",
        "num_rays": 3,
        "rays": [
            {
                "name": "parallel_ray",
                "label": "Ray 1",
                "description": "Parallel to axis -> refracts through F2",
                "draw_back_extension": False,
            },
            {
                "name": "optical_center_ray",
                "label": "Ray 2",
                "description": "Through optical centre -> undeviated",
                "draw_back_extension": False,
            },
            {
                "name": "focal_ray",
                "label": "Ray 3",
                "description": "Through F1 -> emerges parallel to axis",
                "draw_back_extension": False,
            },
        ],
    },
    "inside_f": {
        "image_region": "same_side",
        "ray_mode": "virtual",
        "num_rays": 2,
        "rays": [
            {
                "name": "parallel_ray",
                "label": "Ray 1",
                "description": "Parallel to axis -> diverges through F2; extended back",
                "draw_back_extension": True,
            },
            {
                "name": "optical_center_ray",
                "label": "Ray 2",
                "description": "Through O -> undeviated; extended back",
                "draw_back_extension": True,
            },
        ],
    },
}
