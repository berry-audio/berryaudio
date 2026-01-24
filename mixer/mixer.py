import logging
import alsaaudio
import math
import asyncio
import json
import subprocess

from pathlib import Path
from typing import Optional
from core.actor import Actor
from .utils import aplay_devices

logger = logging.getLogger(__name__)

DTOVERLAY_PATH = Path(__file__).parent.parent / "core" / "util" / "dtoverlay.py"
PLAYBACK_MIXERS_PATH = Path(__file__).parent.parent / "mixer" / "playback_mixers.json"


class MixerExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._output_device = self._config["mixer"]["output_device"]
        self._volume_default = self._config["mixer"]["volume_default"]
        self._volume_muted = False
        self._volume_event_task = None
        self._volume_min = 0
        self._volume_max = 100
        self._mixer = None
        self._loop = asyncio.get_running_loop()

    async def on_config_update(self, config):
        updated_config = config[self._name]
        if "output_device" in updated_config:
            self.on_set_mixer(updated_config.get("output_device"))

    async def on_start(self):
        if self._output_device is None:
            return

        playback_mixer = self.on_get_playback_mixers(self._output_device)
        if playback_mixer is None:
            logger.error(f"No playback mixer found for device '{self._output_device}'")
            return

        volume_control_mixer = playback_mixer.get("volume_control_mixer")
        mixer_index = playback_mixer.get("card_index")

        try:
            self._mixer = alsaaudio.Mixer(
                control=volume_control_mixer, cardindex=mixer_index
            )
            self._loop.create_task(self.on_set_volume(self._volume_default))
            logger.info(
                f"Using mixer control '{volume_control_mixer}', volume set to {self._volume_default}"
            )
        except alsaaudio.ALSAAudioError as e:
            logger.warning(f"Failed to open mixer '{volume_control_mixer}': {e}")

        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

    def on_set_mute(self, mute: bool) -> bool:
        """
        Set mixer mute state.
        """
        self._volume_muted = mute
        if self._mixer is None:
            logger.warning("Mixer is not available")
        else:
            try:
                self._mixer.setmute(int(mute))
                self._volume_muted = self.on_get_mute()
            except alsaaudio.ALSAAudioError as exc:
                if self._mixer:
                    if self._volume_muted:
                        self._mixer.setvolume(0)
                    else:
                        self._mixer.setvolume(
                            self.volume_to_mixer_volume(self._volume_default)
                        )
                    logger.warning(f"Mute failed using volume settings: {exc}")
                else:
                    logger.error(f"Mute failed: {exc}")

            except Exception as exc:
                logger.error(
                    f"Unexpected error while setting mute state or no hardware mute available: {exc}"
                )

        self._core.send(
            target=["web", "bluetooth"],
            event="mixer_mute",
            mute=self._volume_muted,
        )
        logger.info(f"Muted: {self._volume_muted}, Volume: {self._volume_default}")
        return True

    def on_get_mute(self) -> Optional[bool]:
        """
        Get mixer mute state.
        """
        if self._mixer is None:
            logger.warning("Mixer is not available")
        else:
            try:
                channels_muted = self._mixer.getmute()

                if all(channels_muted):
                    self._volume_muted = True
                if not any(channels_muted):
                    self._volume_muted = False

            except alsaaudio.ALSAAudioError as exc:
                logger.warning(f"ALSA error while getting mute state: {exc}")
            except Exception as exc:
                logger.error(
                    f"Unexpected error while getting mute state or no hardware mute available: {exc}"
                )
        return self._volume_muted

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
                    if not self._volume_muted:
                        self._volume_default = self.mixer_volume_to_volume(channels[0])

            except alsaaudio.ALSAAudioError as exc:
                logger.warning(f"ALSA error while getting volume: {exc}")
                return None
            except Exception as exc:
                logger.error(
                    f"Unexpected error while getting volume or no hardware volume available: {exc}"
                )
        return self._volume_default

    async def on_set_volume(self, volume: int = 0) -> bool:
        """
        Set Volume
        """
        self._volume_default = volume
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
                if self._mixer is None:
                    logger.warning("Mixer is not available")

                self._core.send(
                    target="bluetooth", event="volume_changed", volume=volume
                )
                self._core.send(target="web", event="volume_changed", volume=volume)
            except asyncio.CancelledError:
                pass

        if self._mixer is not None:
            asyncio.create_task(_set_volume(self._volume_default))

        self._volume_event_task = asyncio.create_task(
            _delayed_volume_event(self._volume_default)
        )
        return True

    def volume_to_mixer_volume(self, volume):
        if volume == 0:
            return 0
        mixer_volume = (
            self._volume_min + volume * (self._volume_max - self._volume_min) / 100.0
        )
        mixer_volume = 50 * math.log10(mixer_volume)
        return int(mixer_volume)

    def mixer_volume_to_volume(self, mixer_volume):
        volume = mixer_volume
        volume = math.pow(10, volume / 50.0)
        volume = (
            (volume - self._volume_min) * 100.0 / (self._volume_max - self._volume_min)
        )
        return int(volume)

    def on_get_playback_mixers(
        self, device_name: str | None = None
    ) -> list[dict] | dict | None:
        """Return playback mixers, optionally filtered by device name."""

        devices = aplay_devices()
        with open(PLAYBACK_MIXERS_PATH, "r", encoding="utf-8") as f:
            mixers = json.load(f)

        device_map = {d["device"]: d for d in devices}

        _mixers = []
        for mixer in mixers:
            device_info = device_map.get(mixer.get("device"))
            if device_info:
                mixer["card_index"] = device_info.get("card_index")
                mixer["mixer_controls"] = device_info.get("mixer_controls")
            _mixers.append(mixer)

        if device_name:
            for mixer in _mixers:
                if mixer.get("device") == device_name:
                    return mixer
        
        return _mixers

    def on_set_mixer(self, mixer: str):
        with open(PLAYBACK_MIXERS_PATH, "r", encoding="utf-8") as f:
            cards = json.load(f)

        for card in cards:
            if card.get("device") == mixer:
                dtoverlay = card.get("dtoverlay")
                subprocess.run(
                    [
                        "sudo",
                        "/usr/bin/python3",
                        DTOVERLAY_PATH,
                        "#soundcard_overlay",  # make sure this comment exists in dtoverlayfile
                        dtoverlay if dtoverlay else "",
                    ],
                    check=True,
                )
                logger.info(f"dtoverlay is now dtoverlay={dtoverlay}")
