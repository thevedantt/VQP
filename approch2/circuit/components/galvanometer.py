from svg.svg_line import SVGLine
from svg.svg_circle import SVGCircle
from svg.svg_text import SVGText


class Galvanometer:

    HSPAN = 20
    R = 12

    def render(self, x=0, y=0, rotation=0, label=None, **kwargs):
        parts = [
            f'<g transform="translate({x},{y}) rotate({rotation})">',
            SVGLine(-self.HSPAN, 0, -self.R, 0).render(),
            SVGLine(self.R, 0, self.HSPAN, 0).render(),
            SVGCircle(0, 0, self.R).render(),
            SVGText(0, 4, "G", font_size=14, text_anchor="middle").render(),
        ]
        if label:
            parts.append(
                f'<text x="0" y="-{self.R + 8}" font-size="12" '
                f'text-anchor="middle" fill="black">{label}</text>'
            )
        parts.append("</g>")
        return "\n".join(parts)
