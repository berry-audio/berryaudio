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

    def _text_size(self, text):
        tmp = ImageDraw.Draw(Image.new("1", (1, 1)))
        bbox = tmp.textbbox((0, 0), text, font=self.font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _draw_checkerboard(self, draw, x, y, width, height):
        for i in range(width):
            for j in range(height):
                if (i + j) % 2 == 0:
                    draw.point((x + i, y + j), fill=250)

    def draw(self, draw, width=256, y=0, x=0, elapsed=None, total=None):
        progress = 0.0
        if elapsed is not None and total is not None and total > 0:
            progress = min(1.0, elapsed / total)

        # checkerboard for the full bar area
        self._draw_checkerboard(draw, x, y, width, self.bar_height)

        # solid fill for elapsed portion — only if we have valid values
        if progress > 0:
            filled_w = int(width * progress)
            if filled_w > 0:
                draw.rectangle(
                    (x, y, x + filled_w - 1, y + self.bar_height - 1),
                    fill=self.bar_color
                )

        # border
        if self.bar_outline_color:
            draw.rectangle(
                (x, y, x + width - 1, y + self.bar_height - 1),
                outline=self.bar_outline_color,
            )

        # time labels
        if self.show_labels:
            label_y = y - 19
            if elapsed is not None:
                elapsed_str = self._format_time(elapsed)
                draw.text((x, label_y), elapsed_str, font=self.font, fill="white")
            if total is not None:
                total_str = self._format_time(total)
                tw, _ = self._text_size(total_str)
                draw.text((x + width - tw, label_y), total_str, font=self.font, fill="white")