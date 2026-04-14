import logging

from core.actor import SourceActor
from core.models import Track, Source, RefType

logger = logging.getLogger(__name__)


class LineinExtension(SourceActor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._input_device = self._config["linein"]["input_device"] or None
        self._output_device = self._config["mixer"]["output_device"] or None
        self._sample_rate = self._config["linein"]["sample_rate"] or 44100
        self._bit_depth = self._config["linein"]["bit_depth"] or "S16_LE"
        self._gain = self._config["linein"]["gain"] or 0
        self._channels = 2
        self._audio_codec = "PCM"
        self._track = Track(
            uri=self._name,
            name="Line In",
            sample_rate=self._sample_rate,
            bit_depth=self._bit_depth,
            channels=self._channels,
            audio_codec=self._audio_codec,
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
        await self.on_stop_service()
        logger.info("Stopped")

    async def on_start_service(self):
        await self._core.request(
            "dsp.set_capture_device",
            device=self._input_device,
            gain=self._gain,
            samplerate=self._sample_rate,
        )
        await self._core.request("playback.set_metadata", track=self._track)
        logger.info("Started service")
        return self._source

    async def on_stop_service(self):
        await self._core.request("playback.clear")
        logger.info("Stopped service")
        return True
