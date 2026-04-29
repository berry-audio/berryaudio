import logging
import asyncio

from pathlib import Path
from gi.repository import GLib, Gst
from core.actor import Actor
from core.models import Album, Artist, Track, TlTrack
from core.types import PlaybackState

logger = logging.getLogger(__name__)


class PlaybackExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._output_device = self._config["mixer"].get("output_device")
        self._state = PlaybackState.STOPPED
        self._buffering = False
        self._pipeline: None
        self._sink: None
        self._source: None
        self._convert: None
        self._resample: None
        self._capsfilter = None
        self._setup_resample = False
        self._sample_rate = None
        self._duration = 0
        self._elapsed = 0
        self._time_source_id = None
        self._playback_uri = None
        self._playback_ready = False
        self._tl_track = None
        self._loop = asyncio.get_event_loop()

    def _setup_playbin(self, uri: str | None = None):
        self._pipeline = Gst.Pipeline.new("audio-player")
        self._source = Gst.ElementFactory.make("uridecodebin", "source")
        self._convert = Gst.ElementFactory.make("audioconvert", "convert")
        self._resample = Gst.ElementFactory.make("audioresample", "resample")
        self._sink = Gst.ElementFactory.make("alsasink", "sink")

        self._resample.set_property("quality", 0)

        self._sink.set_property("device", self._output_device)
        self._sink.set_property("sync", False)
        self._sink.set_property("buffer-time", 200000)

        for el in [self._source, self._convert, self._resample, self._sink]:
            self._pipeline.add(el)

        self._convert.link(self._resample)
        self._resample.link(self._sink)

        self._source.connect("pad-added", self._on_pad_added)

        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_message)

        if uri:
            self._source.set_property("uri", uri)
        elif self._playback_uri:
            self._source.set_property("uri", self._playback_uri)

    def _on_pad_added(self, decodebin, pad):
        caps = pad.query_caps(None)
        if not caps or caps.is_empty():
            return
        name = caps.get_structure(0).get_name()
        if not name.startswith("audio/"):
            return

        sink_pad = self._convert.get_static_pad("sink")
        if sink_pad.is_linked():
            return

        ret = pad.link(sink_pad)
        if ret != Gst.PadLinkReturn.OK:
            logger.error(f"Pad link failed: {ret}")

        def probe(pad, info):
            caps = pad.get_current_caps()
            if not caps:
                return Gst.PadProbeReturn.OK
            structure = caps.get_structure(0)

            if structure.has_name("audio/x-raw"):
                rate = (
                    structure.get_int("rate")[1]
                    if structure.has_field("rate")
                    else None
                )

                self._sample_rate = rate
                channels = (
                    structure.get_int("channels")[1]
                    if structure.has_field("channels")
                    else None
                )

                bit_depth = None

                if structure.has_field("width"):
                    bit_depth = structure.get_int("width")[1]
                elif structure.has_field("depth"):
                    bit_depth = structure.get_int("depth")[1]
                elif structure.has_field("format"):
                    bit_depth = structure.get_string("format")

                track = self._tl_track.track.copy(
                    update={
                        "sample_rate": rate,
                        "channels": channels,
                        "bit_depth": bit_depth,
                    }
                )
                self._tl_track = TlTrack(tlid=self._tl_track.tlid, track=track)
                self._core.send(
                    target=["web", "display"],
                    event="track_meta_updated",
                    tl_track=self._tl_track,
                )

            return Gst.PadProbeReturn.REMOVE

        pad.add_probe(Gst.PadProbeType.BUFFER, probe)

    def _on_message(self, bus, message):
        t = message.type

        if t == Gst.MessageType.TAG:
            tags = message.parse_tag()
            updates = {}

            for i in range(tags.n_tags()):
                tag_name = tags.nth_tag_name(i)
                for j in range(tags.get_tag_size(tag_name)):
                    value = tags.get_value_index(tag_name, j)

                    if isinstance(value, Gst.Sample):
                        buf = value.get_buffer()
                        result, mapinfo = buf.map(Gst.MapFlags.READ)
                        if result:
                            BASE_DIR = Path(__file__).resolve().parent.parent
                            cover_path = (
                                BASE_DIR
                                / "web"
                                / "www"
                                / "images"
                                / "nowplaying"
                                / "cover.jpg"
                            )
                            with open(cover_path, "wb") as f:
                                f.write(mapinfo.data)
                            buf.unmap(mapinfo)
                            # print("Cover art saved as cover.jpg")
                        continue
                    if tag_name == "audio-codec":
                        updates["audio_codec"] = value
                    elif tag_name == "nominal-bitrate":
                        updates["bitrate"] = value
                    elif tag_name == "bitrate" and not getattr(
                        self._tl_track, "bitrate", None
                    ):
                        updates["bitrate"] = round(value / 1000) * 1000
                    elif tag_name == "title":
                        name = value.strip()
                        if name:
                            updates["name"] = name
                        elif self._tl_track.track.name:
                            updates["name"] = self._tl_track.track.name
                    elif tag_name == "album":
                        updates["albums"] = frozenset([Album(name=value)])
                    elif tag_name == "artist":
                        updates["artists"] = frozenset([Artist(name=value)])
                    elif tag_name == "genre":
                        updates["genre"] = value
                    self._buffering = False

            if updates:
                updated_track = self._tl_track.track.copy(update=updates)
                tl_track = TlTrack(tlid=self._tl_track.tlid, track=updated_track)

                def _has_changes(old: TlTrack, new: TlTrack) -> bool:
                    return old.model_dump_json() != new.model_dump_json()

                if _has_changes(self._tl_track, tl_track):
                    self._tl_track = tl_track
                    self._core.send(
                        target=["web", "display"],
                        event="track_meta_updated",
                        tl_track=self._tl_track,
                    )

        if t == Gst.MessageType.DURATION_CHANGED:
            success, duration = self._pipeline.query_duration(Gst.Format.TIME)
            if success and duration > 0:
                self._duration = int(duration / Gst.SECOND) * 1000
                _track = self._tl_track.track.copy(update={"length": self._duration})
                self._tl_track = TlTrack(tlid=self._tl_track.tlid, track=_track)

        elif t == Gst.MessageType.BUFFERING:
            percent = message.parse_buffering()
            if percent < 100:
                self._pipeline.set_state(Gst.State.PAUSED)
            else:
                self._pipeline.set_state(Gst.State.PLAYING)

            self._core.send(
                target=["web", "display"], event="playback_buffering", percent=percent
            )

        elif t == Gst.MessageType.ASYNC_DONE:
            if not self._playback_ready:
                asyncio.run_coroutine_threadsafe(
                    self._core.request(
                        "dsp.set_capture_device", samplerate=self._sample_rate
                    ),
                    self._loop,
                )
                self._playback_ready = True

        elif t == Gst.MessageType.EOS:
            self.on_stop()
            self._core.send(
                target=["web", "display", "tracklist"],
                event="track_playback_ended",
                tl_track=self._tl_track,
            )

        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            domain = err.domain
            code = err.code
            msg = err.message.lower()

            logger.error(
                f"Domain: {domain}, Code: {code}, Message: {msg}, Debug: {debug}"
            )

            custom_message = "Unknown error"
            if domain == GLib.quark_to_string(Gst.ResourceError.quark()):
                if code == Gst.ResourceError.NOT_FOUND:
                    custom_message = "File not found"
                elif code == Gst.ResourceError.OPEN_READ:
                    custom_message = "Cannot open file"
                elif code == Gst.ResourceError.BUSY:
                    custom_message = "Resource busy"
                else:
                    custom_message = "Resource error"

            elif domain == GLib.quark_to_string(Gst.CoreError.quark()):
                if code == Gst.CoreError.STATE_CHANGE:
                    custom_message = "Failed to start playback"
                elif code == Gst.CoreError.FAILED:
                    custom_message = "Playback pipeline failure"
                elif code == Gst.CoreError.MISSING_PLUGIN:
                    custom_message = "Missing plugin"
                else:
                    custom_message = "Core playback error"

            elif domain == GLib.quark_to_string(Gst.StreamError.quark()):
                if code == Gst.StreamError.DECODE:
                    custom_message = "Unsupported media format"
                elif code == Gst.StreamError.FORMAT:
                    custom_message = "Invalid media format"
                else:
                    custom_message = "Stream error"

            self._core.send(
                target=["web", "display", "tracklist"],
                event="error",
                message=custom_message,
            )

            self.on_stop()

        elif t == Gst.MessageType.STREAM_START:
            if self._playback_ready:
                self._start_time_tracking()

                self._core.send(
                    target=["web", "display"],
                    event="track_playback_started",
                    tl_track=self._tl_track,
                    time_position=self._elapsed,
                )

    def _start_time_tracking(self):
        if self._time_source_id:
            GLib.source_remove(self._time_source_id)

        def update_elapsed():
            if self._pipeline:
                success, position = self._pipeline.query_position(Gst.Format.TIME)
                if success:
                    self._elapsed = int((position / Gst.SECOND) * 1000)
            return True

        self._time_source_id = GLib.timeout_add(500, update_elapsed)

    async def on_start(self):
        self._setup_playbin()
        logger.info("Started")

    async def on_clear(self):
        self._playback_uri = None
        self.on_set_metadata()
        self.on_stop()

    async def on_event(self, message):
        event = message.get("event")

        if event == "dsp_options_changed" or event == "dsp_options_error":
            if self._playback_ready:
                if self._pipeline is not None:
                    self._pipeline.set_state(Gst.State.NULL)
                    await self.on_set_time_position(0)

                self._setup_playbin(uri=self._playback_uri)
                self._play()
                self._now_playing()

        if event == "tracklist_changed":
            if not message["tl_tracks"]:
                self._tl_track = TlTrack(tlid=0, track=self._tl_track.track.copy())

    async def on_get_current_tl_track(self):
        return self._tl_track

    def on_get_state(self):
        return self._state

    def on_set_state(self, state: PlaybackState):
        self._state = state
        self._core.send(
            target=["web", "display"], event="playback_state_changed", state=self._state
        )

    def on_get_time_position(self) -> int:
        return self._elapsed

    async def on_set_time_position(self, position_ms: int):
        self._elapsed = position_ms
        self._core.send(
            target=["web", "display"],
            event="track_position_updated",
            time_position=position_ms,
        )

    def on_set_metadata(self, track: Track | None = None) -> bool:
        if track is None:
            self._tl_track = None
        else:
            tlid = self._tl_track.tlid if self._tl_track else 0
            self._tl_track = TlTrack(tlid=tlid, track=track)

        self._core.send(
            target=["web", "display"],
            event="track_meta_updated",
            tl_track=self._tl_track,
        )
        return True

    async def on_play(self, uri: str | None = None, tlid: int | None = 0) -> bool:
        if uri:
            try:
                ext, path = uri.split(":", 1)
            except ValueError:
                raise ValueError(f"Invalid uri format: {uri}")

            self.on_stop()
            await self._core.request("source.set", uri=ext)

            track = await self._core.request(f"{ext}.lookup_track", path=path)
            if not track:
                raise ValueError("Track metadata lookup failed")

            self._tl_track = TlTrack(tlid=tlid, track=track)

            self._playback_uri = await self._core.request(
                f"{ext}.playback_uri", path=path
            )
            if not self._playback_uri:
                raise ValueError("Playback uri not found")

            if self._playback_uri == ext:
                return True

            self._sample_rate = None
            self._playback_ready = False
            self._setup_playbin(uri=self._playback_uri)

        if self._state == PlaybackState.STOPPED:
            self._pipeline.set_state(Gst.State.PAUSED)
            self._state = PlaybackState.PAUSED
            return self._state

        if self._state == PlaybackState.PAUSED:
            return self._resume()

        if self._state == PlaybackState.PLAYING:
            return self.on_pause()

        return self._state

    def on_seek(self, time_position: int):
        if time_position < 1:
            time_position = 1
        if time_position:
            ms = time_position / 1000
            success = self._pipeline.seek(
                1.0,
                Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                Gst.SeekType.SET,
                ms * Gst.SECOND,
                Gst.SeekType.NONE,
                -1,
            )
            self._elapsed = time_position
            self._core.send(
                target=["web", "display"],
                event="track_position_updated",
                time_position=time_position,
            )
            if success:
                return True
            else:
                return False

    async def on_next(self, from_ui: bool = True) -> bool:
        next_track = await self._core.request("tracklist.next_track", from_ui=from_ui)
        if next_track is not None:
            await self.on_play(next_track.track.uri, next_track.tlid)
        else:
            self.on_stop()
        return True

    async def on_previous(self, from_ui: bool = True) -> bool:
        previous_track = await self._core.request(
            "tracklist.previous_track", from_ui=from_ui
        )
        if previous_track is not None:
            await self.on_play(previous_track.track.uri, previous_track.tlid)
        else:
            self.on_stop()
        return True

    def _resume(self):
        if self._state != PlaybackState.PAUSED:
            return self._state

        if self._pipeline is None:
            return self._state

        self._pipeline.set_state(Gst.State.PLAYING)
        self._state = PlaybackState.PLAYING
        self._start_time_tracking()

        self._core.send(
            target=["web", "display", "tracklist"],
            event="track_playback_resumed",
            tl_track=self._tl_track,
            time_position=self._elapsed,
        )

        self._core.send(
            target=["web", "display"], event="playback_state_changed", state=self._state
        )
        return self._state

    def on_pause(self) -> PlaybackState:
        if self._state != PlaybackState.PLAYING:
            return self._state

        if self._pipeline is None:
            return self._state

        self._pipeline.set_state(Gst.State.PAUSED)

        if self._time_source_id is not None:
            GLib.source_remove(self._time_source_id)
            self._time_source_id = None

        self._state = PlaybackState.PAUSED

        self._core.send(
            target=["web", "display"],
            event="track_playback_paused",
            tl_track=self._tl_track,
            time_position=self._elapsed,
        )
        self._core.send(
            target=["web", "display"],
            event="playback_state_changed",
            state=self._state,
        )

        return self._state

    def on_stop(self) -> PlaybackState:
        if self._pipeline is not None:
            self._pipeline.set_state(Gst.State.NULL)

        if self._state not in (PlaybackState.PLAYING, PlaybackState.PAUSED):
            return self._state

        if self._time_source_id is not None:
            GLib.source_remove(self._time_source_id)
            self._time_source_id = None

        self._state = PlaybackState.STOPPED
        self._playback_ready = False
        self._elapsed = 0

        self._core.send(
            target=["web", "display"],
            event="track_playback_ended",
            tl_track=self._tl_track,
            time_position=self._elapsed,
        )

        self._core.send(
            target=["web", "display"],
            event="playback_state_changed",
            state=self._state,
        )

        return self._state

    def _play(self) -> PlaybackState | bool:
        self._pipeline.set_state(Gst.State.PLAYING)
        self._state = PlaybackState.PLAYING
        self._core.send(
            target=["web", "display"],
            event="playback_state_changed",
            state=self._state,
        )
        return self._state

    def _now_playing(self):
        track = self._tl_track.track
        info = f"Now Playing: {track.name or 'Unknown Title'} : {track.audio_codec} | {track.bitrate}bps | {track.sample_rate}Hz | {track.bit_depth}"
        logger.info(info)
