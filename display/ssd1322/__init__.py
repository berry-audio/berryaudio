import logging
import threading

from PIL import ImageFont, Image
from pathlib import Path

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1322
from luma.core.sprite_system import framerate_regulator

from core.types import DisplayPage, PlaybackState
from display.widgets.vu_meter import WidgetVUMeter
from display.widgets.spectrum_analyzer import WidgetSpectumAnalyzer
from display.widgets.text_scrollable import WidgetTextScrollable
from display.widgets.codec_bitrate import WidgetCodecBitrate
from display.widgets.text_box import WidgetTextBox
from display.widgets.play_pause import WidgetPlayPause
from display.widgets.list_scrollable import WidgetListScrollable
from display.widgets.progress_bar import WidgetProgressBar
from display.widgets.loader import WidgetLoader
from display.utils import format_time, power_state_name

logger = logging.getLogger(__name__)

CAVA_FIFO = "/tmp/cava_fifo"
FONT_STYLE_1 = Path(__file__).parent.parent / "fonts" / "DotMatrix-Custom-5x7.ttf"
FONT_STYLE_2 = Path(__file__).parent.parent / "fonts" / "3x5pexel.ttf"
FONT_STYLE_3 = Path(__file__).parent.parent / "fonts" / "pixChicago.ttf"
FONT_STYLE_4 = Path(__file__).parent.parent / "fonts" / "thin_pixel-7.ttf"

ICON_BLUETOOTH = Path(__file__).parent.parent / "icons" / "bluetooth.png"
ICON_BLUETOOTH_XS = Path(__file__).parent.parent / "icons" / "bluetooth_xs.png"
ICON_SPEAKER = Path(__file__).parent.parent / "icons" / "speaker.png"
ICON_SPOTIFY = Path(__file__).parent.parent / "icons" / "spotify.png"
ICON_AIRPLAY = Path(__file__).parent.parent / "icons" / "airplay.png"
ICON_SHUFFLE = Path(__file__).parent.parent / "icons" / "shuffle.png"
ICON_REPEAT = Path(__file__).parent.parent / "icons" / "repeat.png"
ICON_SINGLE = Path(__file__).parent.parent / "icons" / "single.png"


class DisplaySSD1322:
    def __init__(self, contrast=255):
        self.width = 256
        self.height = 64
        self.serial = spi(device=0, port=0, gpio_DC=24, gpio_RST=25)
        self._device = ssd1322(self.serial, width=self.width, height=self.height)
        self._device.contrast(contrast)
        self.running = False
        self.display_thread = None
        self._bluetooth_connected = False
        self._tuner_stereo = False
        self._volume = 0
        self._muted = False
        self._playback_state = PlaybackState.STOPPED
        self._single = False
        self._repeat = False
        self._shuffle = False
        self._page = None
        self._source = None
        self._power_state = "standby"
        self._blink_visible = False
        self._current_track = None
        self._current_elapsed = 0
        self._current_time = None
        self._current_dir = None
        self._source_dir = None
        self._widget_visualizer = None
        self._visualizer_layout = 1
        self._text_box = WidgetTextBox(font_size=5, font_path=FONT_STYLE_2)
        self._widget_bitrate = WidgetCodecBitrate(font_path=FONT_STYLE_2)
        self._widget_title = WidgetTextScrollable(font_size=33, font_path=FONT_STYLE_1)
        self._widget_artist = WidgetTextScrollable(font_size=21, font_path=FONT_STYLE_1)
        self._widget_play_pause = WidgetPlayPause()
        self.list_scrollable = WidgetListScrollable(
            display_width=self.width,
            display_height=self.height,
            font_size=8,
            font_path=FONT_STYLE_3,
        )
        self.list_scrollable_source = WidgetListScrollable(
            display_width=self.width,
            display_height=self.height,
            font_size=8,
            font_path=FONT_STYLE_3,
            show_counter=False,
        )
        self.progress_bar = WidgetProgressBar(
            font_path=FONT_STYLE_1, font_size=21, bar_height=4, bar_outline_color=False, show_labels=True
        )
        self.loader = WidgetLoader(display_width=self.width, display_height=self.height)

    def _set_power_state(self, state):
        self._power_state = state

    def _set_page(self, page):
        self._page = page

    def _set_source_dir(self, dir, selected_index=0, scroll_offset=0):
        self._source_dir = dir
        self.list_scrollable_source.set_items(
            self._source_dir, selected_index, scroll_offset
        )

    def _get_selected_source(self):
        if self._source_dir is not None:
            return self.list_scrollable_source.get_selected_item()
        return (None, 0, 0)

    def _set_source(self, source):
        self._source = source

    def _set_current_track(self, track):
        self._current_track = track

    def _set_current_elapsed(self, elapsed=0):
        self._current_elapsed = elapsed

    def _set_dir_scroll_up(self):
        self.list_scrollable.scroll_up()
        self.list_scrollable_source.scroll_up()

    def _set_dir_scroll_down(self):
        self.list_scrollable.scroll_down()
        self.list_scrollable_source.scroll_down()

    def _get_selected_item(self):
        if self._current_dir is not None:
            return self.list_scrollable.get_selected_item()
        return (None, 0, 0)

    def _set_dir(self, dir, selected_index=0, scroll_offset=0):
        self._current_dir = dir
        self.list_scrollable.set_items(self._current_dir, selected_index, scroll_offset)

    def _set_playback_state(self, state):
        self._playback_state = state

    def _set_playback_mode(self, single, repeat, shuffle):
        self._single = single
        self._repeat = repeat
        self._shuffle = shuffle

    def _set_volume(self, volume):
        self._volume = volume

    def _set_mute(self, mute):
        self._muted = mute

    def _set_current_time(self, time):
        self._current_time = format_time(time)

    def _set_blink_visible(self, state):
        self._blink_visible = state

    def _set_visualizer_layout(self, layout):
        self._visualizer_layout = layout
        if self._widget_visualizer:
            self._widget_visualizer.cleanup()

        if self._visualizer_layout in [1, 2, 3]:
            self._widget_visualizer = WidgetSpectumAnalyzer(num_bars=64)
        elif self._visualizer_layout == 4:
            self._widget_visualizer = WidgetSpectumAnalyzer(num_bars=128)
        elif self._visualizer_layout in [5, 6]:
            self._widget_visualizer = WidgetVUMeter()

    def init(self):
        self._set_visualizer_layout(1)
        if not self.running:
            self.running = True
            self.display_thread = threading.Thread(
                target=self._handle_messages, daemon=True
            )
            self.display_thread.start()
            logger.info("SSD1322 Display Initialized")

    def stop(self):
        self.running = False
        if self.display_thread is not None and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        self._device.clear()
        logger.info("SSD1322 Display stopped")

    def _handle_messages(self):
        regulator = framerate_regulator(fps=60)

        while self.running:
            with regulator:
                with canvas(self._device) as draw:
                    if self._page == DisplayPage.STANDBY:
                        if self._blink_visible:
                            _time_now = self._current_time
                            self._widget_title.draw(
                                draw,
                                width=self.width,
                                y=12,
                                text=_time_now,
                                center=True,
                            )

                    if self._page == DisplayPage.POWER_STATE_CHANGING:
                        self._widget_title.draw(
                            draw,
                            width=self.width,
                            y=12,
                            text=power_state_name(self._power_state),
                            auto_scroll=False,
                            center=True,
                        )
                    if self._page == DisplayPage.SOURCE_DIRECTORY:
                        self.list_scrollable_source.draw(draw)

                    if self._page == DisplayPage.SOURCE:
                        self._widget_title.draw(
                            draw,
                            width=self.width,
                            y=12,
                            text=self._source.name,
                            auto_scroll=False,
                            center=True,
                        )

                    if self._page == DisplayPage.VOLUME:
                        self._widget_title.draw(
                            draw,
                            width=self.width,
                            y=12,
                            text=f"VOLUME {self._volume}",
                            center=True,
                        )

                    if self._page == DisplayPage.MUTE:
                        self._widget_title.draw(
                            draw,
                            width=self.width,
                            y=12,
                            text=f"MUTE",
                            center=True,
                        )

                    if self._page == DisplayPage.LOADING:
                        self.loader.draw(draw)

                    if self._page == DisplayPage.DIRECTORY:
                        self.list_scrollable.draw(draw)

                    if self._page == DisplayPage.NOW_PLAYING:
                        draw.text(
                            (239, -8),
                            str(self._volume),
                            font=ImageFont.truetype(FONT_STYLE_4, 20),
                            fill="white",
                        )
                        draw.bitmap((232, 0), Image.open(ICON_SPEAKER), fill="white")

                        # if self._bluetooth_connected:
                        #     draw.bitmap(
                        #         (239, 0), Image.open(ICON_BLUETOOTH_XS), fill="white"
                        #     )

                        if self._shuffle:
                            draw.bitmap(
                                (201, 0), Image.open(ICON_SHUFFLE), fill="white"
                            )

                        if self._repeat:
                            draw.bitmap((215, 0), Image.open(ICON_REPEAT), fill="white")

                        if self._single:
                            draw.bitmap((225, 0), Image.open(ICON_SINGLE), fill="white")

                        if (
                            self._current_track is not None
                            and self._current_track.audio_codec
                        ):
                            self._widget_bitrate.draw(
                                draw,
                                235,
                                18,
                                bitrate=self._current_track.bitrate,
                                audio_codec=self._current_track.audio_codec,
                            )

                        if self._current_track is not None and self._current_track.name:
                            self._widget_title.draw(
                                draw,
                                width=214,
                                x=13,
                                y=12,
                                text=self._current_track.name,
                            )
                        else:
                            if self._source and self._source.state:
                                self._widget_title.draw(
                                    draw,
                                    width=256,
                                    x=-3,
                                    y=12,
                                    text=self._source.state.name,
                                )

                        if self._current_track is not None and self._current_track.name:
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
                            if self._current_track is not None and len(
                                self._current_track.artists
                            ):
                                self._widget_artist.draw(
                                    draw,
                                    width=190,
                                    x=-2,
                                    y=-3,
                                    text=next(iter(self._current_track.artists)).name,
                                )
                            else:
                                if self._source and self._source.type:
                                    self._widget_artist.draw(
                                        draw,
                                        width=190,
                                        x=-2,
                                        y=-3,
                                        text=self._source.name,
                                    )

                        if self._tuner_stereo:
                            self._text_box.draw(
                                draw,
                                224,
                                20,
                                box_width=32,
                                box_height=9,
                                text="STEREO",
                                highlight=True,
                            )

                        if self._visualizer_layout == 7:
                            self.progress_bar.draw(
                                draw,
                                width=self.width,
                                y=60,
                                x=0,
                                elapsed=self._current_elapsed,
                                total=(
                                    self._current_track.length
                                    if self._current_track
                                    else None
                                ),
                            )

                        if isinstance(self._widget_visualizer, WidgetSpectumAnalyzer):
                            if self._visualizer_layout == 1:
                                self._widget_visualizer.draw(
                                    draw,
                                    width=self.width,
                                    height=18,
                                    x=0,
                                    y=46,
                                    bar_pattern="solid",
                                    bar_color="white",
                                )
                            elif self._visualizer_layout == 2:
                                self._widget_visualizer.draw(
                                    draw,
                                    width=self.width,
                                    height=18,
                                    x=0,
                                    y=46,
                                    bar_pattern="horizontal_lines",
                                    bar_color="white",
                                )
                            elif self._visualizer_layout == 3:
                                self._widget_visualizer.draw(
                                    draw,
                                    width=self.width,
                                    height=18,
                                    x=0,
                                    y=46,
                                    bar_pattern="horizontal_lines",
                                    bar_color="red",
                                )
                            elif self._visualizer_layout == 4:
                                self._widget_visualizer.draw(
                                    draw,
                                    width=self.width,
                                    height=18,
                                    x=0,
                                    y=46,
                                    bar_pattern="solid",
                                    bar_color="white",
                                )

                        elif isinstance(self._widget_visualizer, WidgetVUMeter):
                            if self._visualizer_layout == 5:
                                self._widget_visualizer.draw(
                                    draw,
                                    width=self.width,
                                    height=16,
                                    x=0,
                                    y=38,
                                    bar_pattern="solid",
                                )
                            elif self._visualizer_layout == 6:
                                self._widget_visualizer.draw(
                                    draw,
                                    width=self.width,
                                    height=16,
                                    x=0,
                                    y=38,
                                    bar_pattern="checkerboard",
                                )
