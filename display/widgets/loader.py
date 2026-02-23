import math

class WidgetLoader:
    def __init__(self, display_width=128, display_height=64):
        self.display_width = display_width
        self.display_height = display_height
        self._loading_frame = 0
        self.spinner_radius = 8
        self.dot_count = 8
        self.animation_speed = 5
    
    def _draw_loading_spinner(self, draw, frame):
        """Draw animated loading spinner"""
        center_x = self.display_width // 2
        center_y = self.display_height // 2 
        
        for i in range(self.dot_count):
            angle = (i * 45) - (frame * 45)
            x = center_x + int(self.spinner_radius * math.cos(math.radians(angle)))
            y = center_y + int(self.spinner_radius * math.sin(math.radians(angle)))
            
            brightness = 255 - (i * 30)
            if brightness < 50:
                brightness = 50
            
            draw.ellipse([x-2, y-2, x+2, y+2], fill=brightness)
    
    def draw(self, draw):
        frame = (self._loading_frame // self.animation_speed) % self.dot_count
        self._draw_loading_spinner(draw, frame)
        self._loading_frame += 1