from core.types import PlaybackState


class WidgetPlayPause:
    def __init__(self, device):
        self._device = device

    def draw(self, draw, x, y, state=PlaybackState.STOPPED):
        icon_width = 7
        icon_height = 11

        if state == PlaybackState.PLAYING:
            for i in range(icon_height):
                line_length = min(i + 1, icon_height - i)
                if line_length > 0:
                    draw.line(
                        [(x, y + i), (x + line_length - 1, y + i)],
                        fill="white",
                        width=1,
                    )
        else:
            bar_width = 2
            gap = 3
            draw.rectangle(
                [(x, y), (x + bar_width - 1, y + icon_height - 1)], fill="white"
            )
            draw.rectangle(
                [(x + bar_width + gap, y), (x + icon_width - 1, y + icon_height - 1)],
                fill="white",
            )
