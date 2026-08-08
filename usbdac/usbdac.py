import logging

from core.actor import SourceActor
from core.models import Track, Source
from core.util.system import SystemUtil

logger = logging.getLogger(__name__)


class UsbdacExtension(SourceActor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._system = SystemUtil(core, db)
        self._input_device = self._config[self._name].get("input_device")
        self._output_device = self._config["mixer"].get("output_device")
        self._sample_rate = self._config[self._name].get("sample_rate")
        self._bit_depth = self._config[self._name].get("bit_depth")
        self._gain = self._config[self._name].get("gain")
        self._channels = 2
        self._audio_codec = "PCM"
        self._track = Track(
            uri=self._name,
            name="USB DAC",
            sample_rate=self._sample_rate,
            bit_depth=self._bit_depth,
            channels=self._channels,
            audio_codec=self._audio_codec,
        )
        self._source = Source(
            name="USB DAC",
            uri=self._name,
            controls=[],
            state={"connected": False},
        )

    async def on_init(self, enable=False):
        await self._system.write_dtoverlay("#usb_mode", "dwc2,dr_mode=peripheral" if enable else "dwc2,dr_mode=host")
        logger.info(f'Enabled in {"peripheral" if enable else "host"} mode')

    async def on_config_update(self, config):
        updated_config = config[self._name]
        if not updated_config:
            return

        if "enable" in updated_config:
            await self.on_init(updated_config["enable"])
            self._core.send(event="system", action="restart")

        if "sample_rate" in updated_config:
            self._sample_rate = updated_config["sample_rate"]
            await self._system.write_g_audio_config(samplerate=self._sample_rate)
            self._track.sample_rate = self._sample_rate
            await self._core.request("playback.set_metadata", track=self._track)
            self._core.send(event="system", action="restart")

        if "gain" in updated_config:
            self._gain = updated_config["gain"]

        if await self.is_active():
            await self._core.request(
                "dsp.set_capture_device",
                device=self._input_device,
                gain=self._gain,
                samplerate=self._sample_rate,
            )

    async def is_active(self):
        source = await self._core.request("source.get")
        return bool(source and source.uri == self._name)

    async def on_start(self):
        await self.on_init(self._config[self._name].get("enable"))
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

    async def on_start_service(self):
        await self._core.request(
            "dsp.set_capture_device",
            device=self._input_device,
            gain=self._gain,
            samplerate=self._sample_rate,
        )
        await self._core.request("playback.set_metadata", track=self._track)
        logger.info("Starting service")
        return self._source

    async def on_stop_service(self):
        await self._core.request("playback.clear")
        logger.info("Stopping service")
        return True
