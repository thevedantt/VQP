import json


class TemplateRetriever:

    def __init__(self):

        with open(
            "data/diagram_library.json",
            "r",
            encoding="utf-8"
        ) as f:

            self.templates = json.load(f)

    def retrieve(self, classification):

        for template in self.templates:

            if (
                template["diagram_type"]
                == classification["diagram_type"]
                and
                template["concept"]
                == classification["concept"]
            ):
                return template

        return None