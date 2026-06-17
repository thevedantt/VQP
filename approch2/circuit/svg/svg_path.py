class SVGPath:

    def __init__(self, d="", stroke="black", stroke_width=2, fill="none"):
        self.d = d
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.fill = fill

    def render(self):
        if not self.d:
            return ""
        return (
            f'<path d="{self.d}" '
            f'stroke="{self.stroke}" '
            f'stroke-width="{self.stroke_width}" '
            f'fill="{self.fill}" />'
        )

    def M(self, x, y):
        self.d += f"M{x},{y}"
        return self

    def L(self, x, y):
        self.d += f"L{x},{y}"
        return self

    def H(self, x):
        self.d += f"H{x}"
        return self

    def V(self, y):
        self.d += f"V{y}"
        return self

    def C(self, x1, y1, x2, y2, x, y):
        self.d += f"C{x1},{y1} {x2},{y2} {x},{y}"
        return self

    def Z(self):
        self.d += "Z"
        return self

    def translate(self, dx, dy):
        parts = []
        tokens = self.d.replace(",", " ").split()
        i = 0
        while i < len(tokens):
            cmd = tokens[i]
            parts.append(cmd)
            i += 1
            if cmd in ("M", "L", "C"):
                if cmd == "C":
                    for _ in range(3):
                        if i + 1 < len(tokens):
                            parts.append(str(float(tokens[i]) + dx))
                            parts.append(str(float(tokens[i + 1]) + dy))
                            i += 2
                else:
                    if i < len(tokens):
                        parts.append(str(float(tokens[i]) + dx))
                        parts.append(str(float(tokens[i + 1]) + dy))
                        i += 2
            elif cmd in ("H",):
                if i < len(tokens):
                    parts.append(str(float(tokens[i]) + dx))
                    i += 1
            elif cmd in ("V",):
                if i < len(tokens):
                    parts.append(str(float(tokens[i]) + dy))
                    i += 1
            elif cmd == "Z":
                pass
            else:
                i += 1
        self.d = " ".join(parts)
        return self
