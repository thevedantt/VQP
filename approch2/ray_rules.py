RULES = {
    "beyond_2f": {
        "image_region": "between_f_and_2f",
        "ray_mode": "real",
        "num_rays": 3,
        "rays": [
            {
                "name": "parallel_ray",
                "label": "Ray 1",
                "description": "Parallel to axis \u2192 refracts through F\u2082",
                "draw_back_extension": False,
            },
            {
                "name": "optical_center_ray",
                "label": "Ray 2",
                "description": "Through optical centre \u2192 undeviated",
                "draw_back_extension": False,
            },
            {
                "name": "focal_ray",
                "label": "Ray 3",
                "description": "Through F\u2081 \u2192 emerges parallel to axis",
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
                "description": "Parallel to axis \u2192 refracts through F\u2082",
                "draw_back_extension": False,
            },
            {
                "name": "optical_center_ray",
                "label": "Ray 2",
                "description": "Through optical centre \u2192 undeviated",
                "draw_back_extension": False,
            },
            {
                "name": "focal_ray",
                "label": "Ray 3",
                "description": "Through F\u2081 \u2192 emerges parallel to axis",
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
                "description": "Parallel to axis \u2192 refracts through F\u2082",
                "draw_back_extension": False,
            },
            {
                "name": "optical_center_ray",
                "label": "Ray 2",
                "description": "Through optical centre \u2192 undeviated",
                "draw_back_extension": False,
            },
            {
                "name": "focal_ray",
                "label": "Ray 3",
                "description": "Through F\u2081 \u2192 emerges parallel to axis",
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
                "description": "Parallel to axis \u2192 diverges through F\u2082; extended back",
                "draw_back_extension": True,
            },
            {
                "name": "optical_center_ray",
                "label": "Ray 2",
                "description": "Through O \u2192 undeviated; extended back",
                "draw_back_extension": True,
            },
        ],
    },
}
