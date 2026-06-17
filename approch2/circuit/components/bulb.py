from svg.svg_line import SVGLine
from svg.svg_circle import SVGCircle


class Bulb:

    HSPAN = 20
    R = 10

    def render(self, x=0, y=0, rotation=0, label=None, **kwargs):
        lines = [
            SVGLine(-self.HSPAN, 0, -self.R, 0).render(),
            SVGLine(self.R, 0, self.HSPAN, 0).render(),
        ]
        circle = SVGCircle(0, 0, self.R)
        cross1 = SVGLine(-self.R * 0.7, -self.R * 0.7,
                         self.R * 0.7, self.R * 0.7).render()
        cross2 = SVGLine(self.R * 0.7, -self.R * 0.7,
                         -self.R * 0.7, self.R * 0.7).render()

        markup = "\n".join(lines + [circle.render(), cross1, cross2])
        parts = [f'<g transform="translate({x},{y}) rotate({rotation})">']
        parts.append(markup)
        if label:
            parts.append(
                f'<text x="0" y="-{self.R + 8}" font-size="12" '
                f'text-anchor="middle" fill="black">{label}</text>'
            )
        parts.append("</g>")
        return "\n".join(parts)
