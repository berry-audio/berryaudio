from PIL import ImageFont, Image
from core.models import RefType
from pathlib import Path

FONT_STYLE_1 = Path(__file__).parent.parent / "fonts" / "3x5pexel.ttf"

ICON_MUSIC_NOTE = Path(__file__).parent.parent / "icons" / "music_note.png"
ICON_DIRECTORY = Path(__file__).parent.parent / "icons" / "directory.png"
ICON_BULLET = Path(__file__).parent.parent / "icons" / "bullet.png"
ICON_STORAGE = Path(__file__).parent.parent / "icons" / "storage.png"
ICON_BLUETOOTH = Path(__file__).parent.parent / "icons" / "bluetooth.png"


class WidgetListScrollable:
    def __init__(
        self,
        display_width=128,
        display_height=64,
        show_counter=True,
        font_path=None,
        font_size=8,
    ):
        self.items = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.width = display_width
        self.height = display_height
        self.show_counter = show_counter

        # Load font
        if font_path:
            try:
                self.font = ImageFont.truetype(
                    font_path, font_size, layout_engine=ImageFont.Layout.BASIC
                )
            except:
                self.font = ImageFont.load_default()
        else:
            self.font = ImageFont.load_default()

        # Calculate layout
        self.line_height = 16
        self.visible_items = self.height // self.line_height
        self.padding_left = 4
        self.scrollbar_width = 4
        self.scrollbar_padding = 2
        self.folder_icon = Image.open(ICON_DIRECTORY)
        self.track_icon = Image.open(ICON_MUSIC_NOTE)
        self.bullet_icon = Image.open(ICON_BULLET)
        self.storage_icon = Image.open(ICON_STORAGE)
        self.bluetooth_icon = Image.open(ICON_BLUETOOTH)

    def set_items(self, items, selected_index=0, scroll_offset=0):
        self.items = items
        self.selected_index = selected_index
        self.scroll_offset = scroll_offset

    def draw(self, draw):
        items = self.items

        if items is None:
            return

        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.visible_items, len(items))
        content_width = self.width - self.scrollbar_width - self.scrollbar_padding
        for i in range(start_idx, end_idx):
            y_pos = (i - start_idx) * self.line_height
            display_name = items[i].name
            display_type = items[i].type
            display_active = getattr(items[i], 'active', False) or getattr(items[i], 'connected', False)

            max_chars = 35
            if len(display_name) > max_chars:
                display_name = display_name[: max_chars - 3] + "..."

            # Selected
            if i == self.selected_index:
                draw.rectangle(
                    [(0, y_pos), (content_width, y_pos + self.line_height)],
                    fill="white",
                    outline="white",
                )

                if display_type == RefType.TRACK:
                    draw.bitmap((2, y_pos + 4), self.track_icon, fill="black")
                elif (
                    display_type == RefType.DIRECTORY
                    or display_type == RefType.ALBUM
                    or display_type == RefType.ARTIST
                ):
                    draw.bitmap((2, y_pos + 4), self.folder_icon, fill="black")
                elif display_type == RefType.STORAGE:
                    draw.bitmap((2, y_pos + 4), self.storage_icon, fill="black")
                elif display_type == RefType.BLUETOOTH:
                    draw.bitmap((2, y_pos + 4), self.bluetooth_icon, fill="black")
                else:
                    draw.bitmap((4, y_pos + 4), self.bullet_icon, fill="black")

                draw.text(
                    (self.padding_left + 12, y_pos + 1),
                    f"{display_name}",
                    font=self.font,
                    fill="black",
                )

            else:
                # Draw normal text
                if display_type == RefType.TRACK:
                    draw.bitmap((2, y_pos + 4), self.track_icon, fill=240)
                elif (
                    display_type == RefType.DIRECTORY
                    or display_type == RefType.ALBUM
                    or display_type == RefType.ARTIST
                ):
                    draw.bitmap((2, y_pos + 4), self.folder_icon, fill=240)
                elif display_type == RefType.STORAGE:
                    draw.bitmap((2, y_pos + 4), self.storage_icon, fill=240)
                    
                elif display_type == RefType.BLUETOOTH:
                    draw.bitmap((2, y_pos + 4), self.bluetooth_icon, fill=240)    
                else:
                    pass
                
                if display_active:
                    if display_type == RefType.BLUETOOTH:
                        draw.bitmap((2, y_pos + 4), self.bluetooth_icon, fill="white")
                    else:     
                        draw.bitmap((4, y_pos + 4), self.bullet_icon, fill="white")

                draw.text(
                    (self.padding_left + 12, y_pos + 1),
                    display_name,
                    font=self.font,
                    fill="white",
                )

        # Draw scrollbar if needed
        if len(self.items) > self.visible_items:
            scrollbar_x = self.width - self.scrollbar_width

            # Draw scrollbar track
            draw.rectangle(
                [(scrollbar_x, 0), (self.width - 1, self.height - 1)], outline="white"
            )

            # Calculate scrollbar thumb size and position
            thumb_height = max(
                8,  # Minimum thumb height
                int((self.visible_items / len(self.items)) * self.height),
            )

            # Calculate thumb position
            scroll_range = self.height - thumb_height
            if len(self.items) > self.visible_items:
                thumb_pos = int(
                    (self.scroll_offset / (len(self.items) - self.visible_items))
                    * scroll_range
                )
            else:
                thumb_pos = 0

            # Draw scrollbar thumb
            draw.rectangle(
                [
                    (scrollbar_x + 1, thumb_pos),
                    (self.width - 2, thumb_pos + thumb_height),
                ],
                fill="white",
            )

        if self.show_counter:
            counter_text = f"{self.selected_index + 1}/{len(self.items)}"
            font = ImageFont.truetype(FONT_STYLE_1, 5, layout_engine=ImageFont.Layout.BASIC)
            
            bbox = font.getbbox(counter_text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            rect_x1 = content_width - 40
            rect_y1 = self.height - 12
            rect_x2 = content_width
            rect_y2 = self.height

            text_x = rect_x1 + (40 - text_w) // 2
            text_y = rect_y1 + (12 - text_h) // 2
            
            draw.rectangle([(rect_x1, rect_y1), (rect_x2, rect_y2)], fill="black", outline="white")
            draw.text((text_x, text_y), counter_text, font=font, fill="white")

    def scroll_down(self):
        if self.items is None:
            return

        if self.selected_index < len(self.items) - 1:
            self.selected_index += 1

            # Adjust scroll offset if needed
            if self.selected_index >= self.scroll_offset + self.visible_items:
                self.scroll_offset = self.selected_index - self.visible_items + 1

            return True
        return False
       

    def scroll_up(self):
        if self.items is None:
            return

        if self.selected_index > 0:
            self.selected_index -= 1

            # Adjust scroll offset if needed
            if self.selected_index < self.scroll_offset:
                self.scroll_offset = self.selected_index

            return True
        return False

    def page_up(self):
        if self.items is None:
            return

        """Jump up by one page"""
        if self.selected_index > 0:
            self.selected_index = max(0, self.selected_index - self.visible_items)
            self.scroll_offset = max(0, self.scroll_offset - self.visible_items)
            return True
        return False

    def page_down(self):
        if self.items is None:
            return

        """Jump down by one page"""
        if self.selected_index < len(self.items) - 1:
            self.selected_index = min(
                len(self.items) - 1, self.selected_index + self.visible_items
            )
            if self.selected_index >= self.scroll_offset + self.visible_items:
                self.scroll_offset = min(
                    len(self.items) - self.visible_items,
                    self.scroll_offset + self.visible_items,
                )
            return True
        return False

    def get_selected_item(self):
        """Returns tuple: (item, selected_index, scroll_offset)"""
        if not self.items or self.selected_index >= len(self.items) or self.selected_index < 0:
            return None
        return self.items[self.selected_index], self.selected_index, self.scroll_offset

    def get_selected_index(self):
        return self.selected_index
