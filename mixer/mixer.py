import logging
import alsaaudio
import math
import asyncio

from typing import Optional
from core.actor import Actor
from .mixer_utils import get_playback_devices

logger = logging.getLogger(__name__)


class MixerExtension(Actor):
    default_config = {
        "output_device": "plughw:CARD=vc4hdmi,DEV=0",
        "output_audio": "plughw:CARD=Loopback,DEV=0",
        "volume_default": 50,
        "volume_software_control": False,
        "volume_device": None,
    }

    def __init__(self, core, db, config):
        super().__init__()
        self._loop = asyncio.get_running_loop()
        self._core = core
        self._db = db
        self._config = config
        self._device = None
        self._initial_volume = None
        self._initial_muted = False
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
                            asyncio.create_task(
                                self._service_handler(
                                    self.on_set_volume(self._initial_volume)
                                )
                            )
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

    def on_set_mute(self, mute: bool) -> bool:
        """
        Set mixer mute state.

        :param mute: True to mute, False to unmute
        :return: True if successful, False if mixer unavailable
        :raises RuntimeError: if ALSA operation fails
        """
        self._initial_muted = mute
        if self._mixer is None:
            logger.warning("Mixer is not available")
        else:
            try:
                self._mixer.setmute(int(mute))
                self._initial_muted = self.on_get_mute()
            except alsaaudio.ALSAAudioError as exc:
                logger.error(f"Setting mute state failed: {exc}")
                raise RuntimeError(f"Setting mute state failed: {exc}") from exc
            except Exception as exc:
                logger.error(
                    f"Unexpected error while setting mute state or no hardware mute available: {exc}"
                )

        self._core.send(
            target=["web", "bluetooth"],
            event="mixer_mute",
            mute=self._initial_muted,
        )
        return True

    def on_get_mute(self) -> Optional[bool]:
        """
        Get mixer mute state.

        :return:
            True  -> all channels muted
            False -> no channels muted
            None  -> mixed state, unavailable mixer, or ALSA error
        """
        if self._mixer is None:
            logger.warning("Mixer is not available")
        else:
            try:
                channels_muted = self._mixer.getmute()

                if all(channels_muted):
                    self._initial_muted = True
                if not any(channels_muted):
                    self._initial_muted = False

            except alsaaudio.ALSAAudioError as exc:
                logger.warning(f"ALSA error while getting mute state: {exc}")
            except Exception as exc:
                logger.error(
                    f"Unexpected error while getting mute state or no hardware mute available: {exc}"
                )
        return self._initial_muted

    def on_get_volume(self) -> Optional[int]:
        """
        Get mixer volume.

        """
        if self._mixer is None:
            logger.warning("Mixer is not available")
        else:
            try:
                channels = self._mixer.getvolume()
                if len(channels):
                    self._initial_volume = self.mixer_volume_to_volume(channels[0])

            except alsaaudio.ALSAAudioError as exc:
                logger.warning(f"ALSA error while getting volume: {exc}")
                return None
            except Exception as exc:
                logger.error(
                    f"Unexpected error while getting volume or no hardware volume available: {exc}"
                )
        return self._initial_volume

    async def on_set_volume(self, volume: int = 0) -> bool:
        """
        Set Volume
        """
        self._initial_volume = volume

        if self._mixer is None:
            logger.warning("Mixer is not available")

        if self._volume_event_task and not self._volume_event_task.done():
            self._volume_event_task.cancel()

        async def _set_volume(volume: int):
            try:
                await asyncio.to_thread(
                    self._mixer.setvolume,
                    self.volume_to_mixer_volume(volume),
                )
            except Exception as exc:
                logger.error(f"Failed to set volume: {exc}")

        async def _delayed_volume_event(volume: int):
            try:
                await asyncio.sleep(0.2)
                self._core.send(
                    target="bluetooth", event="volume_changed", volume=volume
                )
                self._core.send(target="web", event="volume_changed", volume=volume)
            except asyncio.CancelledError:
                pass

        asyncio.create_task(_set_volume(volume))
        self._volume_event_task = asyncio.create_task(_delayed_volume_event(volume))

        return True

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
