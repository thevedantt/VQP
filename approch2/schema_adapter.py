class SchemaAdapter:

    def adapt(self, question, template):

        return {
            "question": question,
            "template_id": template["template_id"],
            "diagram_type": template["diagram_type"],
            "concept": template["concept"],
            "scenario": template["scenario"]
        }