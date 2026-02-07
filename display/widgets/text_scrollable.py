from luma.core.virtual import viewport

class WidgetTextScrollable:
    def __init__(self, device, screen_width=None, font_path=None, font_size=10, 
                 start_pause_duration=120, end_pause_duration=120):
        self.device = device
        self.screen_width = screen_width
        self.font_size = font_size
        self.scroll_offset = 0
        self.scroll_speed = 0.5
        self.auto_scroll = True
        self.pause_frames = 0
        self.start_pause_duration = start_pause_duration  # Pause at beginning
        self.end_pause_duration = end_pause_duration      # Pause at end
        self.last_text = None
        self.virtual_canvas = None
        self.text_width = 0
        self.is_paused_at_end = False
        
        if font_path:
            try:
                from PIL import ImageFont
                self.font = ImageFont.truetype(font_path, font_size)
            except Exception as e:
                print(f"Error loading font: {e}, using default")
                self.font = None
        else:
            self.font = None

    def _prepare_canvas(
        self, text, width, text_color="white", background_color="black"
    ):
        from PIL import Image, ImageDraw

        temp_draw = ImageDraw.Draw(Image.new("1", (1, 1)))
        bbox = temp_draw.textbbox((0, 0), text, font=self.font)
        self.text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        canvas_width = max(width, self.text_width + width)
        mono_canvas = Image.new("1", (canvas_width, text_height + 4), 0)
        mono_draw = ImageDraw.Draw(mono_canvas)
        mono_draw.text((0, 0), text, fill=1, font=self.font)

        self.virtual_canvas = Image.new(
            "RGB", (canvas_width, text_height + 4), background_color
        )
        self.virtual_canvas.paste(text_color, mask=mono_canvas)
        return text_height + 4

    def draw(
        self,
        draw,
        width=256,
        y=0,
        x=0,
        text=None,
        text_color="white",
        background_color="black",
    ):
        display_text = text if text is not None else ""
        if not display_text:
            return

        if display_text != self.last_text:
            self.last_text = display_text
            self.scroll_offset = 0
            self.pause_frames = self.start_pause_duration  # Use start pause
            self.is_paused_at_end = False
            canvas_height = self._prepare_canvas(
                display_text, width, text_color, background_color
            )

        if self.auto_scroll and self.text_width > width:
            if self.pause_frames > 0:
                self.pause_frames -= 1
            else:
                # Calculate the maximum scroll offset (when text end reaches screen edge)
                max_offset = self.text_width - width
                
                if not self.is_paused_at_end:
                    self.scroll_offset += self.scroll_speed
                    
                    # Check if we've reached the end
                    if self.scroll_offset >= max_offset:
                        self.scroll_offset = max_offset
                        self.is_paused_at_end = True
                        self.pause_frames = self.end_pause_duration  # Use end pause
                else:
                    # We've paused at the end, now reset
                    self.scroll_offset = 0
                    self.is_paused_at_end = False
                    self.pause_frames = self.start_pause_duration  # Use start pause
        else:
            self.scroll_offset = 0

        if self.virtual_canvas:
            offset = int(self.scroll_offset)
            clipped = self.virtual_canvas.crop(
                (offset, 0, offset + width, self.virtual_canvas.height)
            )
            draw._image.paste(clipped, (x, y))