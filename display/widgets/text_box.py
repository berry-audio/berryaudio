from PIL import ImageFont

class WidgetTextBox:
    def __init__(self, device, font_path=None):
        self._device = device
        self._font_path = font_path
    
    def draw(
        self,
        draw,
        x,
        y,
        text="",
        font_size=5,
        box_width=21,
        box_height=7,
        highlight=False,
    ):
        font = ImageFont.truetype(self._font_path, font_size)
        
        if highlight:
            draw.rectangle(
                [(x, y), (x + box_width - 1, y + box_height - 1)],
                outline="white",
                fill="white",
            )
            text_color = "black"
        else:
            draw.rectangle(
                [(x, y), (x + box_width - 1, y + box_height - 1)],
                outline="white",
                fill="black",
            )
            text_color = "white"
        
        if text:
            text_bbox = draw.textbbox((0, 0), str(text), font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            text_x = x + (box_width - text_width) // 2
            text_y = y + (box_height - text_height) // 2
            
            draw.text(
                (text_x, text_y),
                str(text),
                fill=text_color,
                font=font,
                anchor="lt",
            )