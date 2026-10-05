import os
import logging
import threading
import json
import asyncio
import subprocess

from pathlib import Path
from core.actor import Actor
from core.types import PlaybackState, Command, EncoderMode, DisplayPage, PlaybackControls
from core.models import Album, Artist, Track, Bluetooth, Category, Storage, Directory, Source, Playlist, Tuner, File, TlTrack, Power
from core.util.system import SystemUtil

from .ssd1322 import DisplaySSD1322
from .ssd1306 import DisplaySSD1306

logger = logging.getLogger(__name__)

CAVA_FIFO = "/tmp/cava_fifo"
DISPLAY_LIST_PATH = Path(__file__).parent.parent / "display" / "display.json"
DISPLAY_OVERLAY_TIMEOUT = 1.0
DISPLAY_BLINK_TIMEOUT = 0.5
BIT_DEPTH_MAPPING = {
    "S16_LE": "16bit",
    "S16": "16bit",
    "S32": "32bit",
    "S24_LE": "24bit",
    "S24_32LE": "32bit",
    "S32_LE": "32bit",
    "S16_BE": "16bit",
    "S24_BE": "24bit",
    "S32_BE": "32bit",
    "S16LE": "16bit",
    "S24LE": "24bit",
    "F32LE": "32bit",
}


class DisplayExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._system = SystemUtil(core, db)
        self._device = None
        self._visualizer_layout = 1
        self._playback_state = PlaybackState.STOPPED
        self._timer_tick = None
        self._position_tick = None
        self._controller = None
        self._single = False
        self._repeat = False
        self._shuffle = False
        self._page = DisplayPage.STANDBY
        self._page_prev = self._page
        self._action = None
        self._volume = 0
        self._muted = False
        self._current_tl_track = None
        self._current_tl_track = None
        self._current_dir = None
        self._current_dir_breadcrumbs = []
        self._source = None
        self._current_time = None
        self._power_state = "standby"
        self._blink_visible = True
        self._timer_timeout = None
        self._timer_blink = None
        self._sample_rate = None
        self._sample_format = None
        self._tracklist = None
        self._cava_process = None
        self._cava_config = None
        self._fifo = None

    def get_bit_depth(self, sample_format):
        if not sample_format:
            return ""
        return BIT_DEPTH_MAPPING.get(sample_format, sample_format)

    async def on_config_update(self, config):
        updated_config = config[self._name]
        if "output_display" in updated_config:
            await self.set_display(updated_config.get("output_display"))

        if "visualizer_layout" in updated_config:
            await self.set_visualizer_layout(updated_config.get("visualizer_layout"))

    async def on_event(self, message):
        if self._controller is None:
            return

        if message and "event" in message:
            event = message["event"]
            if event == "source_changed":
                _source = message.get("source")
                self._controller._set_current_elapsed()
                self.set_source(message.get("source"))
                if _source is not None:
                    self.set_page(DisplayPage.NOW_PLAYING)

            elif event == "source_updated":
                self.set_source(message.get("source"))

            elif event == "track_position_updated":
                self._controller._set_current_elapsed(message.get("time_position"))

            elif event == "command":
                self._action = message.get("action")

                if self._action == Command.NOW_PLAYING:
                    self.set_page(DisplayPage.NOW_PLAYING)

                if self._action == Command.SOURCE:
                    self.set_page(DisplayPage.SOURCE_DIRECTORY)

                if self._action == Command.UP:
                    if self._page == DisplayPage.NOW_PLAYING:
                        await self._core.request("playback.previous")
                    else:
                        self.set_dir_scroll_up()

                if self._action == Command.DOWN:
                    if self._page == DisplayPage.NOW_PLAYING:
                        await self._core.request("playback.next")
                    else:
                        self.set_dir_scroll_down()

                if self._action == Command.SELECT:
                    if self._page == DisplayPage.STANDBY:
                        await self._core.request("system.directory", uri="system:standby")

                    if self._page == DisplayPage.NOW_PLAYING and self._source:
                        if PlaybackControls.PLAY in self._source.controls:
                            await self._core.request("playback.play")

                    elif self._page == DisplayPage.DIRECTORY or self._page == DisplayPage.TRACKLIST or self._page == DisplayPage.POWER:
                        selected_item, selected_index, scroll_offset = (
                            self._controller._get_selected_item()
                        )

                        if selected_item is None:
                            return

                        if isinstance(selected_item, Power):
                            self._current_dir_breadcrumbs = []
                            _ext = selected_item.uri.split(":", 1)[0]
                            self.set_page(DisplayPage.POWER_STATE_CHANGING)
                            self.start_timer(DisplayPage.STANDBY)
                            await self._core.request(
                                f"{_ext}.directory",
                                uri=f"{selected_item.uri}",
                            )

                        if isinstance(selected_item, Source):
                            self.set_page(DisplayPage.LOADING)
                            if selected_item.browsable:
                                if selected_item.uri == 'dsp' or selected_item.uri == 'config':
                                    self.set_page(DisplayPage.DIRECTORY)
                                    return

                                elif selected_item.uri == 'bluetooth':
                                    _current_dir = await self._core.request(
                                        f"{selected_item.uri}.devices",
                                    )

                                elif selected_item.uri == 'multiroom':
                                    _current_dir = []
                                    _current_servers = await self._core.request("multiroom.servers")

                                    for server in _current_servers:
                                        groups = server.status.get(
                                            "server", {}).get("groups", [])

                                        for group in groups:
                                            for client in group.get("clients", []):
                                                host = client.get("host", {})

                                                _current_dir.append({
                                                    "__model__": "Room",
                                                    "name": host.get("name", "Unknown"),
                                                    "uri": host.get("ip", ""),
                                                })
                                    print(_current_dir)
                                    # self.set_dir(_current_dir)
                                    self.set_page(DisplayPage.DIRECTORY)
                                else:
                                    _current_dir = await self._core.request(
                                        f"{selected_item.uri}.directory", uri=f"{selected_item.uri}",
                                    )
                                self.set_dir(_current_dir)
                                self.set_page(DisplayPage.DIRECTORY)
                            else:
                                await self._core.request(
                                    "source.set", uri=selected_item.uri
                                )

                        if (
                            isinstance(selected_item, Category)
                            or isinstance(selected_item, Directory)
                            or isinstance(selected_item, Storage)
                        ):
                            _ext = selected_item.uri.split(":", 1)[0]
                            self.set_page(DisplayPage.LOADING)

                            _current_dir = await self._core.request(
                                f"{_ext}.directory",
                                uri=f"{selected_item.uri}",
                            )
                            self.set_dir(
                                _current_dir, selected_index, scroll_offset)
                            self.set_page(DisplayPage.DIRECTORY)

                        if (
                            isinstance(selected_item, Artist)
                            or isinstance(selected_item, Album)
                        ):
                            _ext = selected_item.uri.split(":", 1)[0]
                            self.set_page(DisplayPage.LOADING)

                            _current_dir = await self._core.request(
                                f"{_ext}.directory",
                                uri=f"{selected_item.uri}:tracks",
                            )
                            self.set_dir(
                                _current_dir, selected_index, scroll_offset)
                            self.set_page(DisplayPage.DIRECTORY)

                        if (isinstance(selected_item, Playlist)):
                            _ext = selected_item.uri.split(":", 1)[0]
                            self.set_page(DisplayPage.LOADING)

                            _current_dir = await self._core.request(
                                f"{_ext}.directory",
                                uri=f"{selected_item.uri}:tracks",
                            )
                            self.set_dir(
                                _current_dir, selected_index, scroll_offset)
                            self.set_page(DisplayPage.DIRECTORY)

                        if (isinstance(selected_item, Track)
                                or isinstance(selected_item, Tuner)
                                or isinstance(selected_item, File)
                                ):
                            if selected_item.uri:
                                self.set_page(DisplayPage.LOADING)
                                await self._core.request(
                                    "playback.play", uri=selected_item.uri
                                )
                                self.set_page(DisplayPage.NOW_PLAYING)

                        if (isinstance(selected_item, TlTrack)):
                            if selected_item.tlid:
                                self.set_page(DisplayPage.LOADING)
                                await self._core.request(
                                    "playback.play", uri=selected_item.track.uri, tlid=selected_item.tlid
                                )
                                self.set_page(DisplayPage.NOW_PLAYING)

                        if (isinstance(selected_item, Bluetooth)):
                            if selected_item.address:
                                self.set_page(DisplayPage.LOADING)
                                if selected_item.connected:
                                    await self._core.request(
                                        "bluetooth.disconnect",
                                        address=f"{selected_item.address}",
                                    )
                                else:
                                    await self._core.request(
                                        "bluetooth.connect",
                                        address=f"{selected_item.address}",
                                    )
                                self.set_page(DisplayPage.DIRECTORY)

                if self._action == Command.BACK:
                    if self._page == DisplayPage.STANDBY:
                        return

                    if self._page == DisplayPage.TRACKLIST:
                        self.set_page(DisplayPage.NOW_PLAYING)
                    elif self._page == DisplayPage.NOW_PLAYING:
                        if self._page_prev == DisplayPage.TRACKLIST:
                            self.set_dir(-1)
                        self.set_page(DisplayPage.DIRECTORY)
                    else:
                        if self._page_prev != DisplayPage.POWER:
                            self.set_dir(-1)
                        self.set_page(DisplayPage.DIRECTORY)

                if self._action == Command.BACK_LONG:
                    _current_dir = await self._core.request(
                        f"system.directory", uri="system",
                    )
                    self.set_dir(_current_dir)
                    self.set_page(DisplayPage.POWER)

                if self._action == Command.RIGHT:
                    if self._page == DisplayPage.NOW_PLAYING:
                        _current_dir = await self._core.request("tracklist.get_tltracks")
                        self.set_dir(_current_dir)
                        self.set_page(DisplayPage.TRACKLIST)
                    elif self._page == DisplayPage.TRACKLIST or self._page == DisplayPage.STANDBY:
                        return
                    else:
                        if self._page == DisplayPage.POWER:
                            self.set_dir(-1)
                        self.set_page(DisplayPage.NOW_PLAYING)

                if self._action == Command.VISUALISER:
                    await self.set_visualizer_layout()

            elif event == "system_time_updated":
                self.set_current_time(message.get("datetime"))

            elif event == "system_power_state_changed":
                self._power_state = message.get("state")
                self._controller._set_power_state(self._power_state)

                if self._power_state is None:
                    self.stop_timer_blink()
                    _current_dir = await self._core.request("source.directory")
                    self.set_dir(_current_dir)
                    self.set_page(DisplayPage.DIRECTORY)

                elif self._power_state == "standby":
                    self.start_timer_blink()

                elif self._power_state == "reboot":
                    self.start_timer(None)

                elif self._power_state == "shutdown":
                    self.start_timer(None)

            elif event == "track_playback_started":
                self.set_current_track(message.get("tl_track"))

            elif event == "track_meta_updated":
                self.set_current_track(message.get("tl_track"))

            elif event == "playback_state_changed":
                state = message.get("state")
                self.set_playback_state(state)
                if state == PlaybackState.PLAYING:
                    self.start_position_tick()
                else:
                    self.stop_position_tick()


            elif event == 'dsp_options_changed':
                self._sample_rate = message.get("sample_rate")
                self._sample_format = self.get_bit_depth(
                    message.get("sample_format"))
                self._controller._set_dsp_state(
                    self._sample_rate, self._sample_format
                )

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

            elif (
                event == "storage_updated"
                or event == "storage_mounted"
                or event == "storage_unmounted"
            ):
                if self._source is not None and self._source.uri == "storage":
                    if len(self._current_dir_breadcrumbs) == 0:
                        _current_dir = await self._core.request("storage.directory")
                        self.set_dir(_current_dir["mounted"])

    async def on_start(self):
        await self.set_display(self._config["display"]["output_display"])
        await self.set_visualizer_layout(
            self._config["display"]["visualizer_layout"])

        mixer_volume = await self._core.request("mixer.get_volume")
        self.set_volume(mixer_volume)

        if self._power_state == "standby":
            self.set_page(DisplayPage.STANDBY)
            self.start_timer_blink()

        logger.info("Started")

    async def on_stop(self):
        if self._timer_blink is not None:
            self._timer_blink.cancel()
            self._timer_blink = None

        self.stop_position_tick()

        if self._controller is not None:
            self._controller.stop()
        logger.info("Stopped")

    async def on_start_cava(self):
        if self._visualizer_layout in [7]:
            return

        if self._cava_process is not None:
            return

        if self._controller is None:
            return

        self._cava_config = self._controller._get_visualizer_config()
        if self._cava_config is None:
            return

        if os.path.exists(CAVA_FIFO):
            os.unlink(CAVA_FIFO)

        os.mkfifo(CAVA_FIFO)

        try:
            self._cava_process = subprocess.Popen(
                ["cava", "-p", self._cava_config],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            logger.info(f"Started CAVA with config {self._cava_config}")

            def log(stream, label):
                for line in iter(stream.readline, ""):
                    line = line.strip()
                    if label == "STDERR":
                        logger.error(f"CAVA {label}: {line}")
                    elif "error" in line.lower():
                        logger.error(f"CAVA {label}: {line}")
                    elif "warning" in line.lower():
                        logger.warning(f"CAVA {label}: {line}")
                    else:
                        logger.debug(f"CAVA {label}: {line}")
                stream.close()

            threading.Thread(
                target=log, args=(self._cava_process.stdout, "STDOUT"), daemon=True
            ).start()
            threading.Thread(
                target=log, args=(self._cava_process.stderr, "STDERR"), daemon=True
            ).start()
            self._controller._start_visualizer_fifo()

        except Exception as e:
            logger.error(f"Error starting CAVA: {e}")
            await self.on_stop_cava()

    async def on_stop_cava(self):
        if self._controller:
            self._controller._stop_visualizer_fifo()

        if self._cava_process:
            if os.path.exists(CAVA_FIFO):
                os.unlink(CAVA_FIFO)

            self._cava_process.terminate()
            self._cava_process.wait()
        self._cava_process = None
        logger.info(f"Stopped CAVA")

    def set_page(self, page):
        self._page_prev = self._page
        self._page = page
        if self._page == DisplayPage.DIRECTORY:
            self._core._request("gpio.set_encoder_mode",
                                mode=EncoderMode.DIRECTION)
        else:
            self._core._request("gpio.set_encoder_mode",
                                mode=EncoderMode.VOLUME)

        if self._controller is not None:
            self._controller._set_page(page)

    def set_source(self, source):
        self._source = source
        if self._controller is not None:
            self._controller._set_source(source)

        if self._source is not None and self._source.uri != source.uri:
            self._controller._set_current_elapsed()

    def set_current_track(self, tl_track):
        self._current_tl_track = tl_track
        if self._controller is not None:
            self._controller._set_current_track(tl_track)

    def set_dir(self, dir=None, selected_index=0, scroll_offset=0):
        if dir is None:
            self._current_dir = None
            self._current_dir_breadcrumbs = []
            selected_index = scroll_offset = 0
        elif dir == -1:
            if len(self._current_dir_breadcrumbs) <= 1:
                return
            prev = self._current_dir_breadcrumbs.pop()
            self._current_dir = prev["items"]
            selected_index = prev["selected_index"]
            scroll_offset = prev["scroll_offset"]
        else:
            dir = list(dir)
            if len(dir) == 0:
                return
            self._current_dir_breadcrumbs.append(
                {
                    "items": self._current_dir,
                    "selected_index": selected_index,
                    "scroll_offset": scroll_offset,
                }
            )
            self._current_dir = dir
            selected_index = scroll_offset = 0

        if self._controller is not None:
            self._controller._set_dir(
                self._current_dir, selected_index, scroll_offset)

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

    async def set_visualizer_layout(self, layout=None):
        if layout is not None:
            self._visualizer_layout = layout
        else:
            self._visualizer_layout = (self._visualizer_layout % 7) + 1

        if self._controller is not None:
            self._controller._set_visualizer_layout(self._visualizer_layout)
            await self.on_stop_cava()
            await self.on_start_cava()

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
        self._timer_timeout = threading.Timer(
            DISPLAY_OVERLAY_TIMEOUT, self.end_timer, args=[redirect_page]
        )
        self._timer_timeout.start()

    def end_timer(self, redirect_page=None):
        if redirect_page is not None:
            self.set_page(redirect_page)
        self._timer_timeout = None

    def start_timer_blink(self):
        if self._timer_blink is not None:
            self._timer_blink.cancel()
        self._timer_blink = threading.Timer(
            DISPLAY_BLINK_TIMEOUT, self.toggle_blink)
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

    def start_position_tick(self):
        if self._position_tick is not None:
            self._position_tick.cancel()

        def on_position(future):
            try:
                position = future.result()
            except Exception as e:
                logger.error(f"Position tick error: {e}")
                return
            if position is not None and self._controller is not None:
                self._controller._set_current_elapsed(position)

        def tick():
            self._position_tick = None
            if self._playback_state != PlaybackState.PLAYING:
                return
            asyncio.run_coroutine_threadsafe(
                self._core.request("playback.get_time_position"), self._loop
            ).add_done_callback(on_position)
            self.start_position_tick()

        self._position_tick = threading.Timer(1.0, tick)
        self._position_tick.start()

    def stop_position_tick(self):
        if self._position_tick is not None:
            self._position_tick.cancel()
            self._position_tick = None    

    def on_get_displays(self) -> list[dict] | dict | None:
        """Return displays, optionally filtered by device name."""
        with open(DISPLAY_LIST_PATH, "r", encoding="utf-8") as f:
            displays = json.load(f)
        return displays

    async def set_display(self, device: str | None = None):
        """Sets display and updates dtoverlay."""
        dtoverlay_anchor = "#display_overlay"

        if (
            device is not None
            and self._device is not None
            and device == self._device.get("device")
        ):
            return

        if self._controller is not None:
            self._controller.stop()
            self._controller = None

        if device is None:
            logger.info("Display disabled")
            self._device = None
            await self._system.write_dtoverlay(dtoverlay_anchor)
            await self._system.write_cmdline()
            await self._system.write_xinitrc()
            return

        with open(DISPLAY_LIST_PATH, "r", encoding="utf-8") as f:
            displays = json.load(f)

        found_display = next(
            (d for d in displays if d.get("device") == device), None)

        if found_display is None:
            logger.warning(
                f"Display device '{device}' not found in display list")
            self._device = None
            return

        self._device = found_display
        await self._system.write_dtoverlay(dtoverlay_anchor, self._device.get("dtoverlay"))
        await self._system.write_cmdline(self._device.get("cmdline"))
        await self._system.write_xinitrc(self._device.get("xrandr"))

        if device == "ssd1322":
            self._controller = DisplaySSD1322(contrast=255)
        elif device == "ssd1306":
            self._controller = DisplaySSD1306(contrast=255)
        elif device in ("waveshare_28_dsi", "generic_hdmi", "generic_dsi"):
            pass
        else:
            logger.error(f"Display device '{device}' not supported")
            self._device = None
            return

        if self._controller is not None:
            self._controller.init()
