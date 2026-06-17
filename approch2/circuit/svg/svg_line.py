class SVGLine:

    def __init__(self, x1=0, y1=0, x2=0, y2=0, stroke="black", stroke_width=2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.stroke = stroke
        self.stroke_width = stroke_width

    def render(self):
        return (
            f'<line x1="{self.x1}" y1="{self.y1}" '
            f'x2="{self.x2}" y2="{self.y2}" '
            f'stroke="{self.stroke}" stroke-width="{self.stroke_width}" />'
        )

    def translate(self, dx, dy):
        self.x1 += dx
        self.y1 += dy
        self.x2 += dx
        self.y2 += dy
        return self

    def __repr__(self):
        return f'SVGLine({self.x1},{self.y1} -> {self.x2},{self.y2})'
