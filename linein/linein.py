import asyncio
import os
import logging

from core.actor import SourceActor
from core.models import Track, TlTrack, Source, RefType
from core.types import PlaybackState
from mixer.alsa_arecord import AlsaArecord

logger = logging.getLogger(__name__)


class LineinExtension(SourceActor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._input_device = self._config["linein"]["input_device"] or None
        self._output_device = self._config["mixer"]["output_audio"] or None
        self._sample_rate = self._config["linein"]["sample_rate"] or 44100
        self._bit_depth = self._config["linein"]["bit_depth"] or "S16_LE"
        self._gain = self._config["linein"]["gain"] or 0
        self._channels = 2
        self._arecord = AlsaArecord(
            core=self._core,
            input_device=self._input_device,
            output_device=self._output_device,
            sample_rate=self._sample_rate,
            bit_depth=self._bit_depth,
            channels=self._channels,
            gain=self._gain,
        )
        self._source = Source(
            name="Line In",
            type=RefType.SOURCE,
            uri=self._name,
            controls=[],
            state={"connected": False},
        )

    async def on_start(self):
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        await self._arecord.stop_service()
        logger.info("Stopped")

    async def on_start_service(self):
        state, sample_rate, bit_depth, channels, audio_codec = await self._arecord.start_service()
        track = Track(
            uri=self._name,
            name="Line In",
            sample_rate=sample_rate,
            bit_depth=bit_depth,
            channels=channels,
            audio_codec=audio_codec,
        )
        self._tl_track = TlTrack(0, track=track)

        await self._core.request("playback.set_metadata", tl_track=self._tl_track)
        logger.info("Line in started: arecord | gain (sox) | aplay")

        return state

    async def on_stop_service(self):
        await self._core.request("playback.stop")
        await self._core.request("playback.clear")
        await self._arecord.stop_service()
        logger.debug("Stopped service")
        return True
