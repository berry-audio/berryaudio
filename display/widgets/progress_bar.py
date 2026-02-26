import logging
from PIL import Image, ImageDraw

logging.getLogger("PIL").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class WidgetProgressBar:
    """
    Progress bar with checkerboard background for unfilled portion,
    solid fill for elapsed, border around the bar, and elapsed / total
    time labels below.
    """
    def __init__(
        self,
        font_path=None,
        font_size=8,
        bar_height=6,
        bar_color="white",
        bar_outline_color="white",
        show_labels=True,
    ):
        self.bar_height = bar_height
        self.bar_color = bar_color
        self.bar_outline_color = bar_outline_color
        self.show_labels = show_labels
        self.font = None
        if font_path:
            try:
                from PIL import ImageFont
                self.font = ImageFont.truetype(font_path, font_size)
            except Exception as e:
                logger.warning(f"Error loading font: {e}, using default")

    def _format_time(self, ms):
        seconds = max(0, int(ms // 1000))
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02d}"

    def _draw_checkerboard(self, draw, x, y, width, height):
        for i in range(width):
            for j in range(height):
                if (i + j) % 2 == 0:
                    draw.point((x + i, y + j), fill=250)

    def draw(self, draw, width=256, y=0, x=0, elapsed=0, total=0):
        progress = 0.0
        if elapsed is not None and total is not None and total > 0:
            progress = min(1.0, elapsed / total)

        self._draw_checkerboard(draw, x, y, width, self.bar_height)

        if progress > 0:
            filled_w = int(width * progress)
            if filled_w > 0:
                draw.rectangle(
                    (x, y, x + filled_w - 1, y + self.bar_height - 1),
                    fill=self.bar_color,
                )

        if self.bar_outline_color:
            draw.rectangle(
                (x, y, x + width - 1, y + self.bar_height - 1),
                outline=self.bar_outline_color,
            )

        if self.show_labels:
            label_y = y - 16
            
            if elapsed is not None:
                elapsed_str = self._format_time(elapsed)
                temp_draw = ImageDraw.Draw(Image.new("1", (1, 1)))
                bbox = temp_draw.textbbox((0, 0), elapsed_str, font=self.font)
                mono_canvas = Image.new("1", (bbox[2], bbox[3]), 0)
                mono_draw = ImageDraw.Draw(mono_canvas)
                mono_draw.text((-bbox[0], -bbox[1]), elapsed_str, fill=1, font=self.font)
                draw._image.paste("white", (x, label_y), mask=mono_canvas)
            
            total_str = self._format_time(total if total is not None else 0)
            
            temp_draw = ImageDraw.Draw(Image.new("1", (1, 1)))
            bbox = temp_draw.textbbox((0, 0), total_str, font=self.font)
            tw = bbox[2] - bbox[0]
            mono_canvas = Image.new("1", (bbox[2], bbox[3]), 0)
            mono_draw = ImageDraw.Draw(mono_canvas)
            mono_draw.text((-bbox[0], -bbox[1]), total_str, fill=1, font=self.font)
            
            draw._image.paste("white", (x + width - tw, label_y), mask=mono_canvas)