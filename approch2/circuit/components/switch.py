from svg.svg_line import SVGLine
from svg.svg_circle import SVGCircle


class Switch:

    HSPAN = 20

    def render(self, x=0, y=0, rotation=0, label=None, state="closed", **kwargs):
        lines = [
            SVGLine(-self.HSPAN, 0, -8, 0).render(),
            SVGLine(8, 0, self.HSPAN, 0).render(),
            SVGCircle(-8, 0, 2, fill="black").render(),
            SVGCircle(8, 0, 2, fill="black").render(),
        ]

        if state == "closed":
            lines.append(SVGLine(-8, 0, 8, 0).render())
        else:
            lines.append(SVGLine(-8, 0, 4, -8).render())

        markup = "\n".join(lines)
        parts = [f'<g transform="translate({x},{y}) rotate({rotation})">']
        parts.append(markup)
        if label:
            parts.append(
                f'<text x="0" y="-16" font-size="12" '
                f'text-anchor="middle" fill="black">{label}</text>'
            )
        parts.append("</g>")
        return "\n".join(parts)
