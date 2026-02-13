import logging
import threading

from PIL import Image, ImageOps
from PIL import ImageFont, Image, ImageDraw
from PIL import ImageFont
from core.types import PlaybackState
from datetime import datetime
from pathlib import Path

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1322
from luma.core.sprite_system import framerate_regulator

from display.widgets.vu_meter import WidgetVUMeter
from display.widgets.spectrum_analyzer import WidgetSpectumAnalyzer
from display.widgets.text_scrollable import WidgetTextScrollable
from display.widgets.codec_bitrate import WidgetCodecBitrate
from display.widgets.text_box import WidgetTextBox
from display.widgets.play_pause import WidgetPlayPause

logger = logging.getLogger(__name__)

CAVA_FIFO = "/tmp/cava_fifo"
FONT_STYLE_1 = Path(__file__).parent.parent / "fonts" / "DotMatrix-Custom-5x7.ttf"
FONT_STYLE_2 = Path(__file__).parent.parent / "fonts" / "lcddot_tr.ttf"
FONT_STYLE_3 = Path(__file__).parent.parent / "fonts" / "thin_pixel-7.ttf"
FONT_STYLE_4 = Path(__file__).parent.parent / "fonts" / "3x5pexel.ttf"
FONT_STYLE_5 = Path(__file__).parent.parent / "fonts" / "LedBus.ttf"


class DisplaySSD1322:
    def __init__(self, visualizer=None, contrast=255):
        self.width = 256
        self.height = 64
        self.visualizer = visualizer
        self.serial = spi(device=0, port=0, gpio_DC=24, gpio_RST=25)
        self._device = ssd1322(self.serial, width=self.width, height=self.height)
        self._device.contrast(contrast)
        self.running = False
        self.display_thread = None
        self._timer_timeout = None
        self._timer_blink = None
        self._blink_visible = True
        self._message = None
        self._volume = 0
        self._muted = False
        self._track = None
        self._playback_state = None
        self._page = "STANDBY"
        self._page_prev = "STANDBY"
        self._source = None
        self._standby = True
        self._current_time = None

        self._widget_bitrate = WidgetCodecBitrate(self._device, font_path=FONT_STYLE_4)
        self._widget_source = WidgetTextBox(self._device, font_path=FONT_STYLE_4)
        self._widget_play_pause = WidgetPlayPause(self._device)
        self._widget_title = WidgetTextScrollable(
            self._device, screen_width=self.width, font_size=33, font_path=FONT_STYLE_1
        )
        self._widget_artist = WidgetTextScrollable(
            self._device, screen_width=self.width, font_size=21, font_path=FONT_STYLE_1
        )
        self._widget_taskbar = ImageFont.truetype(str(FONT_STYLE_3), 23)
        self._widget_spectrum_analyzer = WidgetSpectumAnalyzer(
            self._device, num_bars=64
        )
        # self._widget_vumeter = WidgetVUMeter(self._device)

    def get_png_image(self, png_path, width=256, height=64, position=(0, 0)):
        icon = Image.open(png_path).convert("RGBA")
        icon = icon.resize((width, height))
        background = Image.new("RGBA", self._device.size, "black")
        background.paste(icon, position, icon)
        self._device.display(background.convert("RGB"))

    def set_message(self, message):
        if message and "event" in message:
            event = message["event"]
            if event == "source_changed":
                self._source = message["source"]
                if not self._standby:
                    if self._page != "SOURCE":
                        self._page_prev = self._page
                    self._page = "SOURCE"
                    self.start_timer()

            if event == "source_updated":
                self._source = message["source"]
                print(self._source)

            elif event == "system_time_updated":
                self._current_time = message["datetime"]

            elif event == "system_power_state":
                state = message["state"]
                self._standby = state.get("standby")
                if self._standby:
                    self.start_timer_blink()
                    self._page = "STANDBY"
                else:
                    self.stop_timer_blink()
                    self._page = "NOW_PLAYING"

            elif event == "track_meta_updated":
                self._track = message["tl_track"].track

            elif event == "playback_state_changed":
                self._playback_state = message["state"]
                if self._playback_state == PlaybackState.PLAYING:
                    self._page = "NOW_PLAYING"

            elif event == "mixer_mute":
                self._muted = message["mute"]
                if self._muted:
                    self.start_timer_blink()
                else:
                    self.stop_timer_blink()

            elif event == "volume_changed":
                self._volume = message["volume"]
                if self._page != "VOLUME":
                    self._page_prev = self._page
                self._page = "VOLUME"
                self.start_timer()

            self._message = None

    def format_time(self, timestamp):
        if not timestamp:
            return "--:-- --"

        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"

        dt = datetime.fromisoformat(timestamp)
        am_pm = "AM" if dt.hour < 12 else "PM"
        hour = dt.hour % 12
        if hour == 0:
            hour = 12
        return f"{hour:02d}:{dt.minute:02d} {am_pm}"

    def start_timer(self):
        if self._timer_timeout is not None:
            self._timer_timeout.cancel()
        self._timer_timeout = threading.Timer(2.0, self.end_timer)
        self._timer_timeout.start()

    def end_timer(self):
        self._page = self._page_prev
        self._timer_timeout = None

    def start_timer_blink(self):
        if self._timer_blink is not None:
            self._timer_blink.cancel()
        self._timer_blink = threading.Timer(0.5, self.toggle_blink)
        self._timer_blink.start()

    def toggle_blink(self):
        self._blink_visible = not self._blink_visible
        self._timer_blink = None
        self.start_timer_blink()

    def stop_timer_blink(self):
        if self._timer_blink is not None:
            self._timer_blink.cancel()
            self._timer_blink = None
        self._blink_visible = True

    def init(self):
        if self._standby:
            self._page = "STANDBY"
            self.start_timer_blink()

        if not self.running:
            self.running = True
            self.display_thread = threading.Thread(
                target=self._handle_messages, daemon=True
            )
            self.display_thread.start()
            logger.info("SSD1322 Display Initialized")

    def stop(self):
        self.running = False
        if self._timer_blink is not None:
            self._timer_blink.cancel()
            self._timer_blink = None
        if self.display_thread is not None and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        self._device.clear()
        logger.info("SSD1322 Display stopped")

    def format_source_type(self, source_type):
        if source_type == "local":
            return "LIBRARY"
        if source_type == "radio":
            return "RADIO"
        if source_type == "storage":
            return "Storage"
        if source_type == "spotify":
            return "SPOTIFY"
        if source_type == "shairportsync":
            return "AIRPLAY"
        if source_type == "bluetooth":
            return "BLUETOOTH"

    def _handle_messages(self):
        regulator = framerate_regulator(fps=60)
        speaker_icon = Image.open("/home/pi/berryaudio/display/fonts/speaker.png")
        blue_icon = Image.open("/home/pi/berryaudio/display/fonts/bluetooth.png")
        airplay_icon = Image.open("/home/pi/berryaudio/display/fonts/airplay.png")
        spotify_icon = Image.open("/home/pi/berryaudio/display/fonts/spotify.png")
        repeat_icon = Image.open("/home/pi/berryaudio/display/fonts/repeat.png")
        shuffle_icon = Image.open("/home/pi/berryaudio/display/fonts/shuffle.png")

        while self.running:
            with regulator:
                with canvas(self._device) as draw:
                    if self._page == "STANDBY":
                        if self._blink_visible:
                            _time_now = self.format_time(self._current_time)
                            self._widget_title.draw(
                                draw, width=214, x=60, y=12, text=_time_now
                            )

                    if self._page == "SOURCE":
                        self._widget_title.draw(
                            draw,
                            width=self.width,
                            y=12,
                            text=self.format_source_type(self._source.type),
                            auto_scroll=False,
                            center=True,
                        )

                    if self._page == "VOLUME":
                        self._widget_title.draw(
                            draw, width=214, x=40, y=12, text=f"VOLUME {self._volume}"
                        )

                    if self._page == "NOW_PLAYING" and not self._standby:

                        font = ImageFont.truetype(FONT_STYLE_3, 20)
                        text = str(self._volume)
                        draw.text((239, -8), text, font=font, fill="white")
                        draw.bitmap((232, 0), speaker_icon, fill="white")

                        # draw.bitmap((210, 0), blue_icon, fill="white")
                        # draw.bitmap((200, 0), airplay_icon, fill="white")
                        # draw.bitmap((190, 0), spotify_icon, fill="white")

                        draw.bitmap((219, 0), repeat_icon, fill="white")
                        draw.bitmap((205, 0), shuffle_icon, fill="white")

                        # Reeapt icon
                        # draw.rectangle(
                        #     [(245, 18), (246 + 10, 18 + 10)],
                        #     outline="white",
                        #     fill="white",
                        # )
                        # draw.bitmap((247, 20), repeat_icon, fill="black")

                        if self._track is not None and self._track.audio_codec:
                            self._widget_bitrate.draw(
                                draw,
                                235,
                                18,
                                bitrate=self._track.bitrate,
                                audio_codec=self._track.audio_codec,
                            )

                        if self._track is not None and self._track.name:
                            self._widget_title.draw(
                                draw, width=214, x=13, y=12, text=self._track.name
                            )
                        else:
                            if self._source and self._source.state:
                                self._widget_title.draw(
                                    draw,
                                    width=207,
                                    x=13,
                                    y=12,
                                    text=(
                                        self._source.state.name
                                        if self._source.state.name
                                        else "Ready"
                                    ),
                                )

                        self._widget_play_pause.draw(
                            draw, 0, 22, state=self._playback_state
                        )

                        if self._muted:
                            if self._blink_visible:
                                self._widget_artist.draw(
                                    draw,
                                    width=190,
                                    x=-2,
                                    y=-3,
                                    text="MUTED",
                                )
                        else:
                            if self._track is not None and len(self._track.artists):
                                self._widget_artist.draw(
                                    draw,
                                    width=190,
                                    x=-2,
                                    y=-3,
                                    text=next(iter(self._track.artists)).name,
                                )
                            else:
                                if self._source and self._source.type:
                                    self._widget_artist.draw(
                                        draw,
                                        width=190,
                                        x=-2,
                                        y=-3,
                                        text=self.format_source_type(self._source.type),
                                    )
                        # if self._source and self._source.type:
                        # self._widget_source.draw(
                        #     draw,
                        #     224,
                        #     20,
                        #     box_width=32,
                        #     box_height=9,
                        #     text="STEREO",
                        #     highlight=True,
                        # )

                        # self._widget_source.draw(
                        #         draw,
                        #         224,
                        #         28,
                        #         box_width=32,
                        #         box_height=9,
                        #         text='SHFL',
                        #         highlight=False,
                        #     )

                        self._widget_spectrum_analyzer.draw(
                            draw,
                            width=256,
                            height=18,
                            x=0,
                            y=46,
                            bar_pattern="solid",
                            bar_color="white",
                        )
                        # self._widget_vumeter.draw(
                        #     draw,
                        #     width=229,
                        #     height=16,
                        #     x=0,
                        #     y=38,
                        #     bar_pattern="checkerboard",
                        # )
