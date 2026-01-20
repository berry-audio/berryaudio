import logging
import alsaaudio
import math
import asyncio

from core.actor import Actor
from .mixer_utils import get_playback_devices

logger = logging.getLogger(__name__)


class MixerExtension(Actor):
    default_config = {
        "output_device": "plughw:CARD=Headphones,DEV=0",
        "output_audio": "plughw:CARD=Loopback,DEV=0",
        "volume_default": 50,
        "volume_software_control": False,
        "volume_device": None,
    }

    def __init__(self, core, db, config):
        super().__init__()
        self._core = core
        self._db = db
        self._config = config
        self._device = None
        self._initial_volume = None
        self._mixer = None
        self._min_volume = 0
        self._max_volume = 100
        self._devices = []
        self._volume_event_task = None

    async def on_start(self):
        self._device = self._config["mixer"]["volume_device"]
        self._initial_volume = self._config["mixer"]["volume_default"]

        alsa_mixers = self.on_get_playback_devices()

        for mixer in alsa_mixers:
            mixer_device = mixer.get("device")
            mixer_index = mixer.get("card_index")
            mixer_controls = mixer.get("mixer_controls")

            if mixer_device == self._device:
                logger.info(mixer)
                preferred_controls = ["Digital", "PCM", "Master"]
                for control in preferred_controls:
                    if control in mixer_controls:
                        try:
                            self._mixer = alsaaudio.Mixer(
                                control=control, cardindex=mixer_index
                            )
                            self.on_set_volume(self._initial_volume)
                            logger.info(f"Using mixer control -> {control} ")
                        except alsaaudio.ALSAAudioError as e:
                            logger.warning(f"Failed to open mixer '{control}': {e}")
                            continue
                        break

        logger.info(f"Initial volume is set to {self._initial_volume}")
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

    def on_set_mute(self, mute: int):
        try:
            self._mixer.setmute(int(mute))
            self._core.send(
                target=["web", "bluetooth"], event="mixer_mute", mute=self.on_get_mute()
            )
            return True
        except alsaaudio.ALSAAudioError as exc:
            logger.error(f"Setting mute state failed: {exc}")
            raise RuntimeError(f"Setting mute state failed {exc}")

    def on_get_mute(self):
        try:
            channels_muted = self._mixer.getmute()
        except alsaaudio.ALSAAudioError as exc:
            logger.error(f"Getting mute state failed: {exc}")
            raise RuntimeError(f"Setting mute state failed {exc}")
        if all(channels_muted):
            return True
        elif not any(channels_muted):
            return False
        else:
            return None

    def on_get_volume(self):
        try:
            channels = self._mixer.getvolume()
        except alsaaudio.ALSAAudioError as e:
            return None
        except Exception as e:
            return None
        if not channels:
            return None
        elif channels.count(channels[0]) == len(channels):
            return self.mixer_volume_to_volume(channels[0])
        else:
            return None

    def on_set_volume(self, volume: int = 0):
        self._core.send(target="bluetooth", event="volume_changed", volume=volume)
        self.on_set_mute(False)
        loop = asyncio.get_running_loop()

        loop.create_task(
            asyncio.to_thread(
                self._mixer.setvolume,
                self.volume_to_mixer_volume(volume),
            )
        )
        if self._volume_event_task and not self._volume_event_task.done():
            self._volume_event_task.cancel()

        async def _delayed_volume_event(volume: int):
            try:
                await asyncio.sleep(0.2)
                self._core.send(target="web", event="volume_changed", volume=volume)
            except asyncio.CancelledError:
                pass

        self._volume_event_task = loop.create_task(_delayed_volume_event(volume))
        return volume

    def volume_to_mixer_volume(self, volume):
        if volume == 0:
            return 0
        mixer_volume = (
            self._min_volume + volume * (self._max_volume - self._min_volume) / 100.0
        )
        mixer_volume = 50 * math.log10(mixer_volume)
        return int(mixer_volume)

    def mixer_volume_to_volume(self, mixer_volume):
        volume = mixer_volume
        volume = math.pow(10, volume / 50.0)
        volume = (
            (volume - self._min_volume) * 100.0 / (self._max_volume - self._min_volume)
        )
        return int(volume)

    def on_get_playback_devices(self):
        results = get_playback_devices()
        return results
