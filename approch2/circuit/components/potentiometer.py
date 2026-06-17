from svg.svg_line import SVGLine
from svg.svg_path import SVGPath


class Potentiometer:

    HSPAN = 20

    def render(self, x=0, y=0, rotation=0, label=None, **kwargs):
        lines = [
            SVGLine(-self.HSPAN, 0, -12, 0).render(),
            SVGLine(12, 0, self.HSPAN, 0).render(),
        ]
        path = (SVGPath()
                .M(-12, 0).L(-8, -6).L(-4, 6).L(0, -6).L(4, 6).L(8, -6).L(12, 0))

        arrow = SVGPath().M(2, -14).L(6, -10).L(-2, -10)
        arrow_line = SVGLine(0, -10, 0, 0)

        markup = "\n".join(
            lines + [path.render(), arrow.render(), arrow_line.render()]
        )
        parts = [f'<g transform="translate({x},{y}) rotate({rotation})">']
        parts.append(markup)
        if label:
            parts.append(
                f'<text x="0" y="-22" font-size="12" '
                f'text-anchor="middle" fill="black">{label}</text>'
            )
        parts.append("</g>")
        return "\n".join(parts)
