import RPi.GPIO as GPIO
import logging

from .si4703 import si4703Radio
from core.actor import SourceActor
from core.models import Track, TlTrack, Source, RefType, Artist
from mixer.alsa_arecord import AlsaArecord

logger = logging.getLogger(__name__)

PCM1861_MD_GPIO_PIN = 4
SI4703_RESET_GPIO_PIN = 16
SI4703_ADDR = 0x10


class TunerExtension(SourceActor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._input_device = self._config["tuner"]["input_device"] or None
        self._output_device = self._config["mixer"]["output_audio"] or None
        self._sample_rate = self._config["tuner"]["sample_rate"] or 44100
        self._bit_depth = self._config["tuner"]["bit_depth"] or "S16_LE"
        self._gain = self._config["tuner"]["gain"] or 0
        self._channels = 2
        self._tuner = None
        self._default_channel = 875
        self._tl_track = TlTrack(0, track=Track())
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
            name="Tuner",
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
        state, sample_rate, bit_depth, channels, audio_codec = (
            await self._arecord.start_service()
        )
        track = Track(
            uri=self._name,
            name="Tuner",
            sample_rate=sample_rate,
            bit_depth=bit_depth,
            channels=channels,
            audio_codec=audio_codec,
        )
        self._tl_track = TlTrack(0, track=track)
        await self._core.request("playback.set_metadata", tl_track=self._tl_track)
        await self._init_tuner()

        logger.info("Tuner started: arecord | gain (sox) | aplay")

        return state

    async def on_stop_service(self):
        await self._shutdown_tuner()
        await self._arecord.stop_service()
        await self._core.request("playback.stop")
        await self._core.request("playback.clear")
        logger.debug("Stopped service")
        return True

    async def status(self):
        """Display current tuner status"""
        self._default_channel = self._tuner.si4703GetChannel()
        # volume = self._tuner.si4703GetVolume()
        freq = self._default_channel / 10.0

        self._tuner.si4703ReadRegisters()
        is_stereo = (
            self._tuner.si4703_registers[self._tuner.SI4703_STATUSRSSI]
            & (1 << self._tuner.SI4703_STEREO)
        ) != 0
        rssi = self._tuner.si4703_registers[self._tuner.SI4703_STATUSRSSI] & 0xFF
        channels = 2 if is_stereo else 1
        channels_text = "Stereo" if is_stereo else "Mono"

        _tl_track = self._tl_track.track.copy(
            update={
                "uri": f"{self._name}:{self._default_channel}",
                "name": f"FM {freq:.1f} MHz",
                "channels": channels,
                "artists": frozenset([Artist(name=channels_text)]),
            }
        )
        self._tl_track = TlTrack(tlid=0, track=_tl_track)
        await self._core.request("playback.set_metadata", tl_track=self._tl_track)

        logger.info(
            f"{freq:.1f} MHz | {channels_text} | Signal: {rssi:3d}/127"
        )

    async def _init_tuner(self):
        """PCM1861 custom controller"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PCM1861_MD_GPIO_PIN, GPIO.OUT)
        GPIO.output(PCM1861_MD_GPIO_PIN, GPIO.LOW)
        logger.debug("Audio mux enabled: GPIO taken LOW PCM1861 specific command")

        """Si4703 Reset"""
        self._tuner = si4703Radio(SI4703_ADDR, resetPin=SI4703_RESET_GPIO_PIN)
        self._tuner.si4703Init()
        logger.debug("SI4703 tuner enabled")

        self._tuner.si4703ReadRegisters()
        self._tuner.si4703_registers[self._tuner.SI4703_POWERCFG] |= (
            1 << self._tuner.SI4703_DMUTE
        )
        self._tuner.si4703_registers[self._tuner.SI4703_POWERCFG] |= (
            1 << self._tuner.SI4703_SMUTE
        )
        self._tuner.si4703WriteRegisters()
        self._tuner.si4703SetVolume(15)
        logger.debug("SI4703 registers written")

        if self._tuner:
            self._tuner.si4703SetChannel(self._default_channel)

            await self.status()

    async def _shutdown_tuner(self):
        GPIO.setup(PCM1861_MD_GPIO_PIN, GPIO.IN)
        self._tuner.si4703ShutDown()

    async def on_directory(self):
        pass

    async def on_save(self, freq):
        pass

    async def on_edit(self, id):
        pass

    async def on_delete(self, id):
        pass

    async def on_get_channel(self):
        if self._tuner:
            return self._tuner.si4703GetChannel()

    async def on_set_channel(self, channel):
        if self._tuner and channel:
            self._tuner.si4703SetChannel(channel)
            await self.status()
        return self._tuner.si4703GetChannel()

    async def on_seek_up(self, auto=False):
        if not self._tuner:
            raise ValueError("No hardware tuner found")

        if auto:
            self._tuner.si4703SeekUp()
        else:
            new_channel = self._default_channel + 1
            if new_channel <= 1080:
                self._tuner.si4703SetChannel(new_channel)

        await self.status()
        return True

    async def on_seek_down(self, auto=False):
        if not self._tuner:
            raise ValueError("No hardware tuner found")

        if auto:
            self._tuner.si4703SeekDown()
        else:
            new_channel = self._default_channel - 1
            if new_channel >= 875:
                self._tuner.si4703SetChannel(new_channel)

        await self.status()
        return True
