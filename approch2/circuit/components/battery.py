from svg.svg_line import SVGLine
from svg.svg_text import SVGText


class Battery:

    HSPAN = 20

    def render(self, x=0, y=0, rotation=0, label=None, voltage=None, **kwargs):
        lines = [
            SVGLine(-self.HSPAN, 0, -6, 0).render(),
            SVGLine(-4, -8, -4, 8).render(),
            SVGLine(4, -5, 4, 5).render(),
            SVGLine(6, 0, self.HSPAN, 0).render(),
        ]
        markup = "\n".join(lines)
        parts = [f'<g transform="translate({x},{y}) rotate({rotation})">']
        parts.append(markup)
        if label:
            parts.append(
                f'<text x="0" y="-16" font-size="12" '
                f'text-anchor="middle" fill="black">{label}</text>'
            )
        if voltage is not None:
            parts.append(
                f'<text x="0" y="20" font-size="11" '
                f'text-anchor="middle" fill="black">{voltage}V</text>'
            )
        parts.append(
            f'<text x="-10" y="3" font-size="10" '
            f'text-anchor="middle" fill="black">+</text>'
        )
        parts.append(
            f'<text x="10" y="3" font-size="10" '
            f'text-anchor="middle" fill="black">-</text>'
        )
        parts.append("</g>")
        return "\n".join(parts)
