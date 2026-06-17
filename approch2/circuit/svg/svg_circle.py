class SVGCircle:

    def __init__(self, cx=0, cy=0, r=10, fill="none", stroke="black", stroke_width=2):
        self.cx = cx
        self.cy = cy
        self.r = r
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width

    def render(self):
        return (
            f'<circle cx="{self.cx}" cy="{self.cy}" r="{self.r}" '
            f'fill="{self.fill}" stroke="{self.stroke}" '
            f'stroke-width="{self.stroke_width}" />'
        )

    def translate(self, dx, dy):
        self.cx += dx
        self.cy += dy
        return self
