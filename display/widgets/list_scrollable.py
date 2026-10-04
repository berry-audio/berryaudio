import time

from PIL import ImageFont, Image, ImageDraw
from core.models import TlTrack, Track, Bluetooth, Storage, Directory, Category, File, Playlist, Tuner, Album, Artist
from pathlib import Path

FONT_STYLE_1 = Path(__file__).parent.parent / "fonts" / "3x5pexel.ttf"

ICON_MUSIC_NOTE = Path(__file__).parent.parent / "icons" / "music_note.png"
ICON_DIRECTORY = Path(__file__).parent.parent / "icons" / "directory.png"
ICON_BULLET = Path(__file__).parent.parent / "icons" / "bullet.png"
ICON_STORAGE = Path(__file__).parent.parent / "icons" / "storage.png"
ICON_BLUETOOTH = Path(__file__).parent.parent / "icons" / "bluetooth.png"
ICON_PLAYLIST = Path(__file__).parent.parent / "icons" / "playlist.png"
ICON_TUNER = Path(__file__).parent.parent / "icons" / "tuner.png"
ICON_ALBUM = Path(__file__).parent.parent / "icons" / "album.png"
ICON_ARTIST = Path(__file__).parent.parent / "icons" / "artist.png"

class WidgetListScrollable:
    def __init__(
        self,
        display_width=128,
        display_height=64,
        show_counter=True,
        font_path=None,
        font_size=8,
        marquee_speed=20,   # pixels per second
        marquee_pause=1.0,  # seconds to wait at the start and at the end
    ):
        self.items = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.width = display_width
        self.height = display_height
        self.show_counter = show_counter
        self.marquee_speed = marquee_speed
        self.marquee_pause = marquee_pause
        self._marquee_start = time.monotonic()

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
        self.max_text_width = (
                self.width - self.scrollbar_width - self.scrollbar_padding
                - (self.padding_left + 12) - 2
            )
        self.names = []   # full names (used by the marquee)
        self.labels = []  # names truncated with "..." (used for unselected rows)

        self.folder_icon = Image.open(ICON_DIRECTORY)
        self.track_icon = Image.open(ICON_MUSIC_NOTE)
        self.bullet_icon = Image.open(ICON_BULLET)
        self.storage_icon = Image.open(ICON_STORAGE)
        self.bluetooth_icon = Image.open(ICON_BLUETOOTH)
        self.playlist_icon = Image.open(ICON_PLAYLIST)
        self.tuner_icon = Image.open(ICON_TUNER)
        self.album_icon = Image.open(ICON_ALBUM)
        self.artist_icon = Image.open(ICON_ARTIST)

    def set_items(self, items, selected_index=0, scroll_offset=0):
        self.items = list(items) if items is not None else None
        n = len(self.items) if self.items else 0
        self.names = [None] * n
        self.labels = [None] * n
        self.selected_index = selected_index
        self.scroll_offset = scroll_offset
        self._reset_marquee()
        
    def draw(self, draw):
        items = self.items

        if items is None:
            return

        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.visible_items, len(items))
        content_width = self.width - self.scrollbar_width - self.scrollbar_padding
        for i in range(start_idx, end_idx):
            y_pos = (i - start_idx) * self.line_height

            display_name = self._get_label(i)
            display_active = getattr(items[i], "active", False) or getattr(
                items[i], "connected", False
            )

            # Selected
            if i == self.selected_index:
                draw.rectangle(
                    [(0, y_pos), (content_width - 2, y_pos + self.line_height)],
                    fill="white",
                )
            
                if isinstance(items[i], TlTrack) or isinstance(items[i], Track) or isinstance(items[i], File):
                    draw.bitmap((2, y_pos + 4), self.track_icon, fill="black")

                elif isinstance(items[i], Storage):    
                    draw.bitmap((2, y_pos + 4), self.storage_icon, fill="black")

                elif isinstance(items[i], Tuner):    
                    draw.bitmap((2, y_pos + 4), self.tuner_icon, fill="black")

                elif isinstance(items[i], Album):    
                    draw.bitmap((2, y_pos + 4), self.album_icon, fill="black")

                elif isinstance(items[i], Artist):    
                    draw.bitmap((2, y_pos + 4), self.artist_icon, fill="black")
                
                elif isinstance(items[i], Playlist):    
                    draw.bitmap((2, y_pos + 4), self.playlist_icon, fill="black")    

                elif isinstance(items[i], Directory) or isinstance(items[i], Category): 
                    draw.bitmap((2, y_pos + 4), self.folder_icon, fill="black")

                elif isinstance(items[i], Bluetooth): 
                    draw.bitmap((2, y_pos + 4), self.bluetooth_icon, fill="black")

                else:
                    draw.bitmap((4, y_pos + 4), self.bullet_icon, fill="black")

                if display_name != self.names[i]:
                    # Name does not fit: scroll the full text, no ellipsis
                    self._draw_marquee(draw, self.names[i], y_pos)
                else:
                    draw.text(
                        (self.padding_left + 12, y_pos + 1),
                        display_name,
                        font=self.font,
                        fill="black",
                    )

            else:
                # Draw normal text
                if isinstance(items[i], TlTrack) or isinstance(items[i], Track) or isinstance(items[i], File):
                    draw.bitmap((2, y_pos + 4), self.track_icon, fill=240)

                elif isinstance(items[i], Storage):    
                    draw.bitmap((2, y_pos + 4), self.storage_icon, fill=240)

                elif isinstance(items[i], Tuner):    
                    draw.bitmap((2, y_pos + 4), self.tuner_icon, fill=240)

                elif isinstance(items[i], Album):    
                    draw.bitmap((2, y_pos + 4), self.album_icon, fill=240)

                elif isinstance(items[i], Artist):    
                    draw.bitmap((2, y_pos + 4), self.artist_icon, fill=240)

                elif isinstance(items[i], Playlist):    
                    draw.bitmap((2, y_pos + 4), self.playlist_icon, fill=240)  

                elif isinstance(items[i], Directory) or isinstance(items[i], Category): 
                    draw.bitmap((2, y_pos + 4), self.folder_icon, fill=240)

                elif isinstance(items[i], Bluetooth): 
                    draw.bitmap((2, y_pos + 4), self.bluetooth_icon, fill=240)

                else:
                    draw.bitmap((4, y_pos + 4), self.bullet_icon, fill="black")

                if display_active:
                    if isinstance(items[i], Bluetooth):
                        draw.bitmap((2, y_pos + 4), self.bluetooth_icon, fill="white")

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
            font = ImageFont.truetype(
                FONT_STYLE_1, 5, layout_engine=ImageFont.Layout.BASIC
            )

            bbox = font.getbbox(counter_text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            rect_x1 = content_width - 40
            rect_y1 = self.height - 12
            rect_x2 = content_width
            rect_y2 = self.height

            text_x = rect_x1 + (40 - text_w) // 2
            text_y = rect_y1 + (12 - text_h) // 2

            draw.rectangle(
                [(rect_x1, rect_y1), (rect_x2, rect_y2)], fill="black", outline="white"
            )
            draw.text((text_x, text_y), counter_text, font=font, fill="white")

    def scroll_down(self):
        if self.items is None:
            return

        if self.selected_index < len(self.items) - 1:
            self.selected_index += 1

            # Adjust scroll offset if needed
            if self.selected_index >= self.scroll_offset + self.visible_items:
                self.scroll_offset = self.selected_index - self.visible_items + 1

            self._reset_marquee()
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

            self._reset_marquee()
            return True
        return False

    def page_up(self):
        if self.items is None:
            return

        """Jump up by one page"""
        if self.selected_index > 0:
            self.selected_index = max(0, self.selected_index - self.visible_items)
            self.scroll_offset = max(0, self.scroll_offset - self.visible_items)
            self._reset_marquee()
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
            self._reset_marquee()
            return True
        return False

    def get_selected_item(self):
        """Returns tuple: (item, selected_index, scroll_offset)"""
        if (
            not self.items
            or self.selected_index >= len(self.items)
            or self.selected_index < 0
        ):
            return None
        return self.items[self.selected_index], self.selected_index, self.scroll_offset

    def get_selected_index(self):
        return self.selected_index

    def is_marquee_active(self):
        """True while the selected name is too long to fit and is scrolling.
        The caller should keep redrawing while this is True."""
        if not self.items or not (0 <= self.selected_index < len(self.items)):
            return False
        return self.labels[self.selected_index] != self.names[self.selected_index]

    def _reset_marquee(self):
        self._marquee_start = time.monotonic()

    def _draw_marquee(self, draw, name, y_pos):
        text_w = int(self.font.getlength(name)) + 1
        overflow = text_w - self.max_text_width   # pixels hidden at the right
        travel_time = overflow / self.marquee_speed

        now = time.monotonic()
        t = now - self._marquee_start

        # pause at start -> scroll -> pause at end -> jump back and repeat
        if t > self.marquee_pause * 2 + travel_time:
            self._marquee_start = now
            t = 0

        if t <= self.marquee_pause:
            offset = 0
        else:
            offset = min(overflow, int((t - self.marquee_pause) * self.marquee_speed))

        # Render the full text to a 1-bit strip, crop the visible window, and
        # draw it as a mask. This clips the text so it never touches the scrollbar.
        h = self.line_height - 2
        strip = Image.new("1", (text_w, h), 0)
        ImageDraw.Draw(strip).text((0, 0), name, font=self.font, fill=1)
        strip = strip.crop((offset, 0, offset + self.max_text_width, h))

        draw.bitmap((self.padding_left + 12, y_pos + 1), strip, fill="black")

    def _item_name(self, item):
        name = item.track.name if isinstance(item, TlTrack) else item.name
        return name or ""

    def _truncate(self, name):
        if self.font.getlength(name) <= self.max_text_width:
            return name

        lo, hi = 0, len(name)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.font.getlength(name[:mid] + "...") <= self.max_text_width:
                lo = mid
            else:
                hi = mid - 1
        return name[:lo] + "..."

    def _get_label(self, i):
        label = self.labels[i]
        if label is None:
            name = self._item_name(self.items[i])
            self.names[i] = name
            label = self.labels[i] = self._truncate(name)
        return label