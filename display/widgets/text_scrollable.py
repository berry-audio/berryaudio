import logging

from luma.core.virtual import viewport
from PIL import Image, ImageDraw

logging.getLogger("PIL").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class WidgetTextScrollable:
    def __init__(self, font_path=None, font_size=10, 
                 start_pause_duration=120, end_pause_duration=120):
        self.font_size = font_size
        self.scroll_offset = 0
        self.scroll_speed = 0.5
        self.pause_frames = 0
        self.start_pause_duration = start_pause_duration
        self.end_pause_duration = end_pause_duration
        self.last_text = None
        self.virtual_canvas = None
        self.text_width = 0
        self.text_height = 0
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

    def _prepare_canvas(self, text, width, text_color="white", background_color="black"):
       

        temp_draw = ImageDraw.Draw(Image.new("1", (1, 1)))
        bbox = temp_draw.textbbox((0, 0), text, font=self.font)
        self.text_width = bbox[2] - bbox[0]
        self.text_height = bbox[3] - bbox[1]
        
        canvas_width = max(width, self.text_width + width)
        canvas_height = self.text_height + 4
        
        mono_canvas = Image.new("1", (canvas_width, canvas_height), 0)
        mono_draw = ImageDraw.Draw(mono_canvas)
        mono_draw.text((0, 0), text, fill=1, font=self.font)
        
        self.virtual_canvas = Image.new("RGB", (canvas_width, canvas_height), background_color)
        self.virtual_canvas.paste(text_color, mask=mono_canvas)
        
        return canvas_height

    def draw(self, draw, width=256, y=0, x=0, text=None, 
             text_color="white", background_color="black", auto_scroll=True, center=False):
        display_text = text if text is not None else ""
        
        if not display_text:
            return
        
        if display_text != self.last_text:
            self.last_text = display_text
            self.scroll_offset = 0
            self.pause_frames = self.start_pause_duration
            self.is_paused_at_end = False
            canvas_height = self._prepare_canvas(display_text, width, text_color, background_color)
        
        if auto_scroll and self.text_width > width:
            if self.pause_frames > 0:
                self.pause_frames -= 1
            else:
                max_offset = self.text_width - width
                
                if not self.is_paused_at_end:
                    self.scroll_offset += self.scroll_speed
                    
                    if self.scroll_offset >= max_offset:
                        self.scroll_offset = max_offset
                        self.is_paused_at_end = True
                        self.pause_frames = self.end_pause_duration
                else:
                    self.scroll_offset = 0
                    self.is_paused_at_end = False
                    self.pause_frames = self.start_pause_duration
        else:
            self.scroll_offset = 0
        
        if self.virtual_canvas:
            offset = int(self.scroll_offset)
            clipped = self.virtual_canvas.crop((offset, 0, offset + width, self.virtual_canvas.height))
            
            x_offset = x
            if center and self.text_width < width:
                x_offset = x + (width - self.text_width) // 2
            
            draw._image.paste(clipped, (x_offset, y))