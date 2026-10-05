import logging

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class WidgetText:
    """Static text with left / center / right alignment. No scrolling."""

    def __init__(self, font_path=None, font_size=10):
        self.font_size = font_size
        if font_path:
            try:
                self.font = ImageFont.truetype(font_path, font_size)
            except Exception as e:
                logger.warning(f"Error loading font: {e}, using default")
                self.font = None
        else:
            self.font = None

    def draw(self, draw, width=256, y=0, x=0, text=None,
             text_color="white", align="left"):
        """
        Draw text inside the box starting at x, `width` pixels wide.
        align: "left", "center" or "right".
        Text wider than `width` is clipped at the box edge.
        """
        if not text:
            return

        text_width = draw.textlength(text, font=self.font)

        if text_width > width:
            # Too wide: draw into a strip exactly `width` wide so it is
            # clipped at the box edge instead of spilling into neighbours.
            bbox = draw.textbbox((0, 0), text, font=self.font)
            strip = Image.new("1", (width, bbox[3] + 1), 0)
            ImageDraw.Draw(strip).text((0, 0), text, font=self.font, fill=1)
            draw.bitmap((x, y), strip, fill=text_color)
            return

        if align == "right":
            x_pos = x + width - text_width - 3
        elif align == "center":
            x_pos = x + (width - text_width) / 2
        else:
            x_pos = x

        draw.text((int(x_pos), y), text, font=self.font, fill=text_color)