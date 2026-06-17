class SVGText:

    def __init__(self, x=0, y=0, text="", font_size=14,
                 text_anchor="middle", fill="black",
                 font_family="Arial, sans-serif"):
        self.x = x
        self.y = y
        self.text = text
        self.font_size = font_size
        self.text_anchor = text_anchor
        self.fill = fill
        self.font_family = font_family

    def render(self):
        if not self.text:
            return ""
        return (
            f'<text x="{self.x}" y="{self.y}" '
            f'font-size="{self.font_size}" '
            f'text-anchor="{self.text_anchor}" '
            f'font-family="{self.font_family}" '
            f'fill="{self.fill}">'
            f'{self._escape(self.text)}</text>'
        )

    def _escape(self, s):
        return (str(s)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

    def translate(self, dx, dy):
        self.x += dx
        self.y += dy
        return self
