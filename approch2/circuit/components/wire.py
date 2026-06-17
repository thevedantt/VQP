from svg.svg_line import SVGLine


class Wire:

    HSPAN = 20

    def render(self, x=0, y=0, rotation=0, label=None, **kwargs):
        lines = []
        lines.append(
            SVGLine(-self.HSPAN, 0, self.HSPAN, 0).render()
        )
        markup = "\n".join(lines)
        parts = [f'<g transform="translate({x},{y}) rotate({rotation})">']
        parts.append(markup)
        if label:
            parts.append(
                f'<text x="0" y="-12" font-size="12" '
                f'text-anchor="middle" fill="black">'
                f'{label}</text>'
            )
        parts.append("</g>")
        return "\n".join(parts)
