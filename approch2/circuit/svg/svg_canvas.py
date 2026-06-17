class SVGCanvas:

    def __init__(self, width=800, height=600, viewbox=None):
        self.width = width
        self.height = height
        self.viewbox = viewbox or f"0 0 {width} {height}"
        self.elements = []

    def add(self, element):
        self.elements.append(element)
        return self

    def add_markup(self, markup):
        if markup:
            self.elements.append(markup)
        return self

    def render(self):
        lines = [
            '<?xml version="1.0" encoding="utf-8" standalone="no"?>',
            '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"',
            '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">',
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width}pt" height="{self.height}pt" '
            f'viewBox="{self.viewbox}" version="1.1">',
        ]

        for el in self.elements:
            if isinstance(el, str):
                lines.append("  " + el)
            else:
                rendered = el.render()
                if rendered:
                    lines.append("  " + rendered)

        lines.append("</svg>")
        return "\n".join(lines)

    def save(self, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.render())
