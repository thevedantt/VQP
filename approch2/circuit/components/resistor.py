from svg.svg_line import SVGLine


class Resistor:

    HSPAN = 20
    W = 15
    AMP = 6

    def render(self, x=0, y=0, rotation=0, label=None, value=None, **kwargs):
        lines = [
            SVGLine(-self.HSPAN, 0, -self.W, 0).render()
        ]

        segments = 5
        seg_w = (2 * self.W) / segments
        cx = -self.W
        for i in range(segments):
            x2 = cx + seg_w
            y2 = -self.AMP if i % 2 == 0 else self.AMP
            if i == 0:
                y2 = 0
            if i == segments - 1:
                y2 = 0
            lines.append(
                SVGLine(cx, 0 if i == 0 else (-self.AMP if (i - 1) % 2 == 0 else self.AMP),
                        cx + seg_w, y2).render()
            )
            cx = cx + seg_w

        lines.append(
            SVGLine(self.W, 0, self.HSPAN, 0).render()
        )

        markup = "\n".join(lines)
        parts = [f'<g transform="translate({x},{y}) rotate({rotation})">']
        parts.append(markup)
        label_parts = []
        if label:
            label_parts.append(label)
        if value is not None:
            label_parts.append(str(value) + chr(937))
        label_text = " ".join(label_parts)
        if label_text:
            parts.append(
                f'<text x="0" y="-14" font-size="12" '
                f'text-anchor="middle" fill="black">'
                f'{label_text}</text>'
            )
        parts.append("</g>")
        return "\n".join(parts)
