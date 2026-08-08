import logging
import subprocess
import threading
import asyncio
import os

from pathlib import Path
from core.actor import SourceActor
from core.models import Album, Artist, Track, Image, TlTrack, Source
from core.types import PlaybackState

logger = logging.getLogger(__name__)

LIBRESPOT_PATH = "/usr/local/bin/librespot"
ON_EVENT_PATH = Path(__file__).parent / "events.py"


class SpotifyExtension(SourceActor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._hostname = self._config.get("system", {}).get("hostname")
        self._bitrate = str(self._config.get("spotify", {}).get("bitrate", ""))
        self._volume_default = str(
            self._config.get("spotify", {}).get("volume_default", "")
        )
        self._volume_normalization = self._config.get("spotify", {}).get(
            "volume_normalization"
        )
        self._output_device = self._config.get("spotify", {}).get("output_device")
        self._channels = 2
        self._proc = None
        self._track = None
        self._tl_track = None
        self._timer = None
        self._timer_running = True
        self._timer_paused = False
        self._elapsed_timer_count = 0
        self._sample_rate = 44100
        self._bit_depth = "S32"
        self._audio_codec = "Ogg Vorbis (lossy audio codec)"
        self._backend = "alsa"
        self._source = Source(
            name="Spotify Connect",
            uri=self._name,
            controls=[],
            state={"connected": False},
        )
        self._source_active = False

    async def on_start(self):
        if not os.path.exists(LIBRESPOT_PATH):
            logger.error("Librespot service missing")
            return

        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        await self.on_stop_service()
        logger.info("Stopped")

    async def on_stop_service(self):
        await self._core.request("playback.clear")
        self._source_active = False
        await self._stop_timer()

        if self._proc is not None:
            self._proc.terminate()
            self._proc.kill()
        logger.info("Stopping service")
        return True

    async def on_start_service(self):
        self._source_active = True
        if os.path.exists(LIBRESPOT_PATH):
            await self._core.request(
                "dsp.set_capture_device", samplerate=self._sample_rate
            )
            threading.Thread(target=self._librespot_init, daemon=True).start()
            await self._meta_init()

            logger.info(
                f"Starting service"
            )
            logger.info(
                f"Started Spotify Connect with {self._hostname} on {self._output_device}"
            )
        else:
            logger.error(f"Librespot service missing")
        return self._source

    async def _meta_init(self):
        """Reset metadata handling"""
        track = Track(
            uri=self._name,
            name="Spotify Connect",
            sample_rate=self._sample_rate,
            bit_depth=self._bit_depth,
            channels=self._channels,
            audio_codec=self._audio_codec,
        )
        self._track = track
        await self._core.request("playback.set_metadata", track=self._track)

    async def on_message(self, event):
        """Handle incoming events from librespot"""
        logger.debug(event)

        if "PLAYER_EVENT" in event and self._source_active:
            if event["PLAYER_EVENT"] in ("session_connected"):
                self._source.state.user_name = event["USER_NAME"]
                self._source.state.connection_id = event["CONNECTION_ID"]
                self._source.state.connected = True
                self._core.send(
                    target=["web", "display"],
                    event="spotify_connected",
                    name=self._source.state.user_name or "Unknown",
                )
                logger.info(
                    f"Connected to Spotify account: {self._source.state.user_name}"
                )

            if event["PLAYER_EVENT"] in ("session_disconnected"):
                if "connection_id" in self._source.state:
                    if event["CONNECTION_ID"] == self._source.state.connection_id:
                        self._source.state.connected = False
                await self._stop_timer()
                await self._meta_init()
                await self._core.request("playback.stop")
                await self._core.request("source.update_source", source=self._source)
                self._core.send(
                    target=["web", "display"],
                    event="spotify_disconnected",
                    name=self._source.state.user_name or "Unknown",
                )
                logger.warning(
                    f"Disconnected from Spotify account: {self._source.state.user_name}"
                )

            if event["PLAYER_EVENT"] in ("session_client_changed"):
                self._source.state.name = (
                    self._source.state.user_name
                )  # event["CLIENT_NAME"] not available anymore
                await self._stop_timer()
                await self._meta_init()
                await self._core.request(
                    "playback.set_state", state=PlaybackState.STOPPED
                )
                await self._core.request("playback.set_time_position", position_ms=0)
                await self._core.request("source.update_source", source=self._source)

            if event["PLAYER_EVENT"] in ("seeked", "position_correction"):
                await self._core.request(
                    "playback.set_time_position", position_ms=int(event["POSITION_MS"])
                )
                self._elapsed_timer_count = (
                    int(event["POSITION_MS"]) / 1000
                )  # milliseconds to seconds

            if event["PLAYER_EVENT"] in ("seeked", "position_correction"):
                await self._core.request(
                    "playback.set_time_position", position_ms=int(event["POSITION_MS"])
                )
                self._core.send(
                    target=["web", "display"],
                    event="track_position_updated",
                    time_position=int(event["POSITION_MS"]),
                )

            if event["PLAYER_EVENT"] in ("playing"):
                await self._resume_timer()
                await self._core.request(
                    "playback.set_state", state=PlaybackState.PLAYING
                )
                self._core.send(
                    target=["web", "display"],
                    event="track_playback_resumed",
                    tl_track=self._tl_track,
                    time_position=int(event["POSITION_MS"]),
                )

            if event["PLAYER_EVENT"] in ("paused"):
                self._elapsed_timer_count = int(event["POSITION_MS"]) / 1000
                await self._pause_timer()
                await self._core.request(
                    "playback.set_state", state=PlaybackState.PAUSED
                )
                await self._core.request(
                    "playback.set_time_position", position_ms=int(event["POSITION_MS"])
                )
                self._core.send(
                    target=["web", "display"],
                    event="track_playback_paused",
                    tl_track=self._tl_track,
                    time_position=int(event["POSITION_MS"]),
                )

            if event["PLAYER_EVENT"] in (
                "end_of_track",
                "unavailable",
                "preload_next",
                "preloading",
                "loading",
                "stopped",
            ):
                pass  # TODO

            if event["PLAYER_EVENT"] in ("volume_changed"):
                pass  # TODO

            if event["PLAYER_EVENT"] in ("track_changed"):
                covers = event["COVERS"]
                image = covers.split("\n")[0] if covers else "/images/no_cover.jpg"

                if self._track is not None:
                    await self._stop_timer()
                    await self._core.request("playback.stop")

                self._track = Track(
                    uri=event["URI"] or "",
                    name=event["NAME"] or "Unknown",
                    artists=frozenset([Artist(name=event["ARTISTS"] or "")]),
                    albums=frozenset([Album(name=event["ALBUM"] or "")]),
                    composers=frozenset(),
                    performers=frozenset(),
                    track_no=int(event["NUMBER"]) or 0,
                    disc_no=int(event["DISC_NUMBER"]) or 0,
                    length=int(event["DURATION_MS"]) or 0,
                    bitrate=int(self._bitrate) * 1000,
                    sample_rate=self._sample_rate,
                    bit_depth=self._bit_depth,
                    channels=2,
                    audio_codec=self._audio_codec,
                    images=[Image(uri=image)] or [],
                )
                self._tl_track = TlTrack(tlid=0, track=self._track)

                await self._start_timer()
                await self._core.request("playback.set_metadata", track=self._track)
                self._core.send(
                    target=["web", "display"],
                    event="track_playback_started",
                    tl_track=self._tl_track,
                )

    def _librespot_init(self):
        cmd = [
            LIBRESPOT_PATH,
            "--bitrate",
            self._bitrate,
            "--name",
            self._hostname,
            "--format",
            self._bit_depth,
            "--cache",
            "/tmp/spotify_cache",
            "--disable-audio-cache",
            "--backend",
            self._backend,
            "--onevent",
            ON_EVENT_PATH,
            "--initial-volume",
            self._volume_default,
            "--enable-volume-normalisation" if self._volume_normalization else "",
            "--device-type",
            "avr",
            "--device",
            self._output_device,
        ]
        self._proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
        )

        def log(stream, label):
            for line in iter(stream.readline, ""):
                if "error" in line.strip().lower():
                    # self._core.send(event="error", message=line.strip())
                    logger.error(line.strip())
                else:
                    logger.debug(line.strip())
            stream.close()

        threading.Thread(
            target=log, args=(self._proc.stdout, "STDOUT"), daemon=True
        ).start()
        threading.Thread(
            target=log, args=(self._proc.stderr, "STDERR"), daemon=True
        ).start()

    async def _pause_timer(self):
        """Pause track elapsed timer"""
        self._timer_paused = True

    async def _resume_timer(self):
        """Resume track elapsed timer"""
        self._timer_paused = False

    async def _stop_timer(self):
        """Stop track elapsed timer"""
        self._timer_running = False
        self._timer_paused = False
        self._elapsed_timer_count = 0
        if self._timer:
            self._timer.cancel()
            self._timer = None

    async def _start_timer(self):
        """Start track elapsed timer"""
        self._timer_running = True
        self._timer_paused = False
        self._elapsed_timer_count = 0
        self._timer = asyncio.create_task(self._elapsed_timer())

    async def _elapsed_timer(self):
        """Set track position every second"""
        try:
            while self._timer_running:
                if not self._timer_paused:
                    self._elapsed_timer_count += 1
                    await self._core.request(
                        "playback.set_time_position",
                        position_ms=int(self._elapsed_timer_count * 1000),
                    )
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
