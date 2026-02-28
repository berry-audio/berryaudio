import logging
import asyncio
from logging import config
import threading
import subprocess
import json

from pathlib import Path
from core.actor import Actor
from core.types import PlaybackState, GpioActions, EncoderMode, DisplayPage
from core.models import RefType

from .ssd1322 import DisplaySSD1322
from .ssd1306 import DisplaySSD1306

logger = logging.getLogger(__name__)

DTOVERLAY_PATH = Path(__file__).parent.parent / "core" / "util" / "dtoverlay.py"
DISPLAY_LIST_PATH = Path(__file__).parent.parent / "display" / "display.json"


class DisplayExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._device = None
        self._visualizer_layout = self._config["display"]["visualizer_layout"]
        self._loop = asyncio.get_running_loop()
        self._playback_state = PlaybackState.STOPPED
        self._controller = None
        self._single = False
        self._repeat = False
        self._shuffle = False
        self._page = DisplayPage.STANDBY
        self._page_prev = self._page
        self._gpio_key = None
        self._volume = 0
        self._muted = False
        self._current_track = None
        self._current_dir = None
        self._source_dir = None
        self._current_dir_breadcrumbs = []
        self._source = None
        self._current_time = None
        self._power_state = "standby"
        self._blink_visible = True
        self._timer_timeout = None
        self._timer_blink = None

    async def on_config_update(self, config):
        updated_config = config[self._name]
        if "output_display" in updated_config:
            if updated_config.get("output_display") != self._device.get("device"):
                self.set_display(updated_config.get("output_display"))
                
        if "visualizer_layout" in updated_config:    
            self.set_visualizer_layout(updated_config.get("visualizer_layout"))

    async def on_event(self, message):
        if self._controller is None:
            return

        if message and "event" in message:
            event = message["event"]
            if event == "source_changed":
                self.set_source(message.get("source"))
                if self._power_state is None:
                    if self._page != DisplayPage.SOURCE:
                        self._page_prev = self._page
                    self._controller._set_current_elapsed()
                    self._current_dir_breadcrumbs = []
                    self.set_dir()
                    self.set_page(DisplayPage.SOURCE)
                    self.start_timer(DisplayPage.NOW_PLAYING)

            elif event == "source_updated":
                self.set_source(message.get("source"))

            elif event == "track_position_updated":
                self._controller._set_current_elapsed(message.get("time_position"))

            elif event == "gpio_state_changed":
                self._gpio_key = message.get("key")

                if self._gpio_key == GpioActions.NOW_PLAYING:
                    self.set_page(DisplayPage.NOW_PLAYING)

                if self._gpio_key == GpioActions.SOURCE:
                    if self._page != DisplayPage.SOURCE_DIRECTORY:
                        if self._page_prev != DisplayPage.DIRECTORY:
                            self._page_prev = self._page

                        if self._power_state == "standby":
                            await self._core.request("system.standby")

                        source_list = await self._core.request("source.directory")
                        self.set_source_dir(source_list)
                        self.set_page(DisplayPage.SOURCE_DIRECTORY)

                    elif self._page_prev != DisplayPage.STANDBY:
                        self.set_page(self._page_prev)

                if self._gpio_key == GpioActions.UP:
                    self.set_dir_scroll_up()

                if self._gpio_key == GpioActions.DOWN:
                    self.set_dir_scroll_down()

                if self._gpio_key == GpioActions.SELECT:
                    if self._page == DisplayPage.NOW_PLAYING:
                        self._core.send(
                            target=["web", "display"],
                            event="gpio_state_changed",
                            key=GpioActions.DIRECTORY,
                        )

                    if self._page == DisplayPage.SOURCE_DIRECTORY:
                        selected_item, selected_index, scroll_offset = (
                            self._controller._get_selected_source()
                        )
                        if selected_item.active:
                            self.set_page(DisplayPage.NOW_PLAYING)
                        else:
                            await self._core.request(
                                "source.set", uri=selected_item.uri
                            )

                    elif self._page == DisplayPage.DIRECTORY:
                        selected_item, selected_index, scroll_offset = (
                            self._controller._get_selected_item()
                        )
                        if selected_item is not None:
                            if (
                                selected_item.type == RefType.DIRECTORY
                                or selected_item.type == RefType.STORAGE
                                or selected_item.type == RefType.ALBUM
                                or selected_item.type == RefType.ARTIST
                            ):
                                self._current_dir_breadcrumbs.append(
                                    {
                                        "items": self._current_dir,
                                        "selected_index": selected_index,
                                        "scroll_offset": scroll_offset,
                                    }
                                )

                            if selected_item.type == RefType.TRACK:
                                if selected_item.uri:
                                    self.set_page(DisplayPage.LOADING)
                                    await self._core.request(
                                        "playback.play", uri=selected_item.uri
                                    )
                                    self.set_page(DisplayPage.NOW_PLAYING)

                            elif selected_item.type == RefType.DIRECTORY:
                                if selected_item.uri:
                                    self.set_page(DisplayPage.LOADING)
                                    _current_dir = await self._core.request(
                                        f"{self._source.uri}.directory",
                                        uri=f"{selected_item.uri}",
                                    )
                                    self.set_dir(_current_dir)
                                    self.set_page(DisplayPage.DIRECTORY)

                            elif (
                                selected_item.type == RefType.ALBUM
                                or selected_item.type == RefType.ARTIST
                            ):
                                if selected_item.uri:
                                    self.set_page(DisplayPage.LOADING)
                                    _current_dir = await self._core.request(
                                        "local.directory",
                                        uri=f"{selected_item.uri}:list",
                                    )
                                    self.set_dir(_current_dir)
                                    self.set_page(DisplayPage.DIRECTORY)

                            elif selected_item.type == RefType.BLUETOOTH:
                                if selected_item.address:
                                    self.set_page(DisplayPage.LOADING)
                                    if selected_item.connected:
                                        try:
                                            await self._core.request(
                                                "bluetooth.disconnect",
                                                address=f"{selected_item.address}",
                                            )
                                        except Exception as e:
                                            pass
                                        finally:
                                            self.set_page(DisplayPage.DIRECTORY)
                                    else:
                                        try:
                                            await self._core.request(
                                                "bluetooth.connect",
                                                address=f"{selected_item.address}",
                                            )
                                        except Exception as e:
                                            pass
                                        finally:
                                            self.set_page(DisplayPage.NOW_PLAYING)

                            elif selected_item.type == RefType.STORAGE:
                                if selected_item.uri:
                                    self.set_page(DisplayPage.LOADING)
                                    _current_dir = await self._core.request(
                                        "storage.directory", uri=f"{selected_item.uri}"
                                    )
                                    self.set_dir(_current_dir)
                                    self.set_page(DisplayPage.DIRECTORY)

                if self._gpio_key == GpioActions.BACK:
                    if self._current_dir_breadcrumbs:
                        last_items = self._current_dir_breadcrumbs[-1]["items"]
                        last_selected_index = self._current_dir_breadcrumbs[-1][
                            "selected_index"
                        ]
                        last_scroll_offset = self._current_dir_breadcrumbs[-1][
                            "scroll_offset"
                        ]

                        if len(self._current_dir_breadcrumbs) == 1:
                            if self._source.uri == "storage":
                                _current_dir = await self._core.request(
                                    "storage.directory"
                                )
                                last_items = _current_dir["mounted"]
                                last_selected_index = 0
                                last_scroll_offset = 0

                        self.set_dir(
                            last_items, last_selected_index, last_scroll_offset
                        )
                        self.set_page(DisplayPage.DIRECTORY)
                        self._current_dir_breadcrumbs.pop()

                if self._gpio_key == GpioActions.DIRECTORY:
                    if self._timer_timeout is not None:
                        self._timer_timeout.cancel()

                    if self._page == DisplayPage.DIRECTORY:
                        self._page_prev = DisplayPage.NOW_PLAYING
                        self.set_page(self._page_prev)
                        return
                    else:
                        self._page_prev = self._page

                        _current_dir = None
                        if self._source is not None:
                            if self._source.uri == "radio":
                                if self._current_dir is None:
                                    self.set_page(DisplayPage.LOADING)
                                    _current_dir = await self._core.request(
                                        "radio.directory", uri="radio"
                                    )
                                    self.set_dir(_current_dir)

                            elif self._source.uri == "local":
                                if self._current_dir is None:
                                    self.set_page(DisplayPage.LOADING)
                                    _current_dir = await self._core.request(
                                        "local.directory"
                                    )
                                    self.set_dir(_current_dir)

                            elif self._source.uri == "storage":
                                if self._current_dir is None:
                                    self.set_page(DisplayPage.LOADING)
                                    _current_dir = await self._core.request(
                                        "storage.directory"
                                    )
                                    self.set_dir(_current_dir["mounted"])

                            elif self._source.uri == "bluetooth":
                                if self._current_dir is None:
                                    self.set_page(DisplayPage.LOADING)
                                    _current_dir = await self._core.request(
                                        "bluetooth.devices"
                                    )
                                    self.set_dir(_current_dir)

                            elif self._source.uri == "snapcast":
                                if self._current_dir is None:
                                    self.set_page(DisplayPage.LOADING)
                                    _current_dir = await self._core.request(
                                        "snapcast.servers"
                                    )
                                    self.set_dir(_current_dir)

                            if self._current_dir is not None:
                                self.set_page(DisplayPage.DIRECTORY)

                if self._gpio_key == GpioActions.VISUALISER:
                    self.set_visualizer_layout()

            elif event == "system_time_updated":
                self.set_current_time(message.get("datetime"))

            elif event == "system_power_state_changed":
                self._power_state = message.get("state")
                self._controller._set_power_state(self._power_state)

                if self._power_state is None:
                    self.stop_timer_blink()
                    source_list = await self._core.request("source.directory")
                    self.set_source_dir(source_list)
                    self.set_page(DisplayPage.SOURCE_DIRECTORY)

                elif self._power_state == "standby":
                    self.set_page(DisplayPage.POWER_STATE_CHANGING)
                    self.start_timer(DisplayPage.STANDBY)
                    self.start_timer_blink()

                elif self._power_state == "reboot":
                    self.set_page(DisplayPage.POWER_STATE_CHANGING)
                    self.start_timer(None)

                elif self._power_state == "shutdown":
                    self.set_page(DisplayPage.POWER_STATE_CHANGING)
                    self.start_timer(None)

            elif event == "track_meta_updated":
                self.set_current_track(message.get("tl_track").track)

            elif event == "playback_state_changed":
                self.set_playback_state(message.get("state"))

                if self._playback_state == PlaybackState.PLAYING:
                    self.set_page(DisplayPage.NOW_PLAYING)

            elif (
                event == "bluetooth_device_connected"
                or event == "bluetooth_device_disconnected"
            ):
                if self._source is not None and self._source.uri == "bluetooth":
                    _current_dir = await self._core.request("bluetooth.devices")
                    self.set_dir(_current_dir)

            elif event == "options_changed":
                self._single = message.get("single")
                self._repeat = message.get("repeat")
                self._shuffle = message.get("shuffle")
                self._controller._set_playback_mode(
                    self._single, self._repeat, self._shuffle
                )

            elif event == "mixer_mute":
                self.set_mute(message.get("mute"))
                if self._muted:
                    if self._page != DisplayPage.MUTE:
                        if self._page != DisplayPage.VOLUME:
                            self._page_prev = self._page

                    self.set_page(DisplayPage.MUTE)
                    self.start_timer(self._page_prev)
                    self.start_timer_blink()
                else:
                    self.stop_timer_blink()

            elif event == "volume_changed":
                self.set_volume(message.get("volume"))
                if self._page != DisplayPage.VOLUME:
                    if self._page != DisplayPage.MUTE:
                        self._page_prev = self._page
                self.set_page(DisplayPage.VOLUME)
                self.start_timer(self._page_prev)

            elif event == "storage_updated":
                if self._source is not None and self._source.uri == "storage":
                    if len(self._current_dir_breadcrumbs) == 0:
                        _current_dir = await self._core.request("storage.directory")
                        self.set_dir(_current_dir["mounted"])

    async def on_start(self):
        if self._power_state == "standby":
            self.set_page(DisplayPage.STANDBY)
            self.start_timer_blink()

        self.set_display(self._config["display"]["output_display"])
        self.set_visualizer_layout(self._config["display"]["visualizer_layout"])
        logger.info("Started")

    async def on_stop(self):
        if self._timer_blink is not None:
            self._timer_blink.cancel()
            self._timer_blink = None
        if self._controller is not None:
            self._controller.stop()
        logger.info("Stopped")

    def set_page(self, page):
        self._page = page
        if self._page in (DisplayPage.SOURCE_DIRECTORY, DisplayPage.DIRECTORY):
            self._core._request("gpio.set_encoder_mode", mode=EncoderMode.DIRECTION)
        else:
            self._core._request("gpio.set_encoder_mode", mode=EncoderMode.VOLUME)
        if self._controller is not None:
            self._controller._set_page(page)

    def set_source(self, source):
        self._source = source
        if self._controller is not None:
            self._controller._set_source(source)

        if self._source is not None and self._source.uri != source.uri:
            self._current_dir_breadcrumbs = []
            self.set_dir()
            self._controller._set_current_elapsed()

    def set_source_dir(self, dir, selected_index=0, scroll_offset=0):
        self._source_dir = dir
        if self._controller is not None:
            self._controller._set_source_dir(
                self._source_dir, selected_index, scroll_offset
            )

    def set_current_track(self, track):
        self._current_track = track
        if self._controller is not None:
            self._controller._set_current_track(track)

    def set_dir(self, dir=None, selected_index=0, scroll_offset=0):
        self._current_dir = dir
        if self._controller is not None:
            self._controller._set_dir(self._current_dir, selected_index, scroll_offset)

    def set_playback_state(self, state):
        self._playback_state = state
        if self._controller is not None:
            self._controller._set_playback_state(state)

    def set_volume(self, volume):
        self._volume = volume
        if self._controller is not None:
            self._controller._set_volume(volume)

    def set_mute(self, mute):
        self._muted = mute
        if self._controller is not None:
            self._controller._set_mute(mute)

    def set_blink_visible(self, state):
        self._blink_visible = state
        if self._controller is not None:
            self._controller._set_blink_visible(state)

    def set_current_time(self, date_time):
        self._current_time = date_time
        if self._controller is not None:
            self._controller._set_current_time(self._current_time)

    def set_visualizer_layout(self, layout=None):
        if layout is not None:
            self._visualizer_layout = layout
        else:
            self._visualizer_layout = (self._visualizer_layout % 7) + 1
        if self._controller is not None:
            self._controller._set_visualizer_layout(self._visualizer_layout)
        logger.info(f"Visualizer Layout {self._visualizer_layout}")

    def set_dir_scroll_down(self):
        if self._controller is not None:
            self._controller._set_dir_scroll_down()

    def set_dir_scroll_up(self):
        if self._controller is not None:
            self._controller._set_dir_scroll_up()

    def start_timer(self, redirect_page=None):
        if self._timer_timeout is not None:
            self._timer_timeout.cancel()
        self._timer_timeout = threading.Timer(1.0, self.end_timer, args=[redirect_page])
        self._timer_timeout.start()

    def end_timer(self, redirect_page=None):
        if redirect_page is not None:
            self.set_page(redirect_page)
        self._timer_timeout = None

    def start_timer_blink(self):
        if self._timer_blink is not None:
            self._timer_blink.cancel()
        self._timer_blink = threading.Timer(0.5, self.toggle_blink)
        self._timer_blink.start()

    def toggle_blink(self):
        self.set_blink_visible(not self._blink_visible)
        self._timer_blink = None
        self.start_timer_blink()

    def stop_timer_blink(self):
        if self._timer_blink is not None:
            self._timer_blink.cancel()
            self._timer_blink = None
        self.set_blink_visible(True)

    def on_get_displays(self) -> list[dict] | dict | None:
        """Return displays, optionally filtered by device name."""
        with open(DISPLAY_LIST_PATH, "r", encoding="utf-8") as f:
            displays = json.load(f)
        return displays

    def set_display(self, device: str):
        if device is None:
            logger.info("Display disabled")
            self._device = None
            self._controller = None
            return

        with open(DISPLAY_LIST_PATH, "r", encoding="utf-8") as f:
            displays = json.load(f)

        found_display = next(
            (d for d in displays if d.get("device") == device), None
        )

        if found_display is None:
            logger.warning(f"Display device '{device}' not found in display list")
            self._device = None
            self._controller = None
            return

        self._device = found_display
        device = self._device.get("device")
        dtoverlay = self._device.get("dtoverlay")

        subprocess.run(
            [
                "sudo",
                "/usr/bin/python3",
                DTOVERLAY_PATH,
                "#display_overlay",
                dtoverlay if dtoverlay else "",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.debug(f"dtoverlay={dtoverlay}")

        if self._controller is not None:
            self._controller.stop()
            self._controller = None

        if device == "ssd1322":
            self._controller = DisplaySSD1322(contrast=255)

        elif device == "ssd1306":
            self._controller = DisplaySSD1306(contrast=255)

        elif device == "ws28dsilcd":
            self._controller = None

        else:
            logger.error(f"Display device '{device}' not supported")
            self._device = None
            self._controller = None
            return

        if self._controller is not None:
            self._controller.init()

            