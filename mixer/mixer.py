import logging
import alsaaudio
import math
import asyncio
import json
import subprocess

from pathlib import Path
from typing import Optional

from .utils import aplay_devices
from core.actor import Actor
from core.util.system import SystemUtil


logger = logging.getLogger(__name__)

PLAYBACK_MIXERS_PATH = Path(__file__).parent.parent / "mixer" / "playback_mixers.json"
VOL_MIN = 0
VOL_MAX = 100


class MixerExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._system = SystemUtil(core, db)
        self._hw_device = self._config["mixer"]["hw_device"]
        self._volume = self._config["mixer"]["volume_default"]
        self._muted = False
        self._volume_event_task = None
        self._mixer = None
        self._loop = asyncio.get_running_loop()

    async def on_config_update(self, config):
        updated_config = config[self._name]
        if "hw_device" in updated_config:
            await self.set_mixer(updated_config.get("hw_device"))

    async def on_start(self):
        if self._hw_device is None:
            return

        playback_mixer = self.on_get_playback_mixers(self._hw_device)
        if playback_mixer is None:
            logger.error(f"No playback mixer found for device '{self._hw_device}'")
            return

        volume_control_mixer = playback_mixer.get("volume_control_mixer")
        mixer_index = playback_mixer.get("card_index")

        try:
            self._mixer = alsaaudio.Mixer(
                control=volume_control_mixer, cardindex=mixer_index
            )
            self._loop.create_task(self.on_set_volume(self._volume))
            logger.info(
                f"Using mixer control '{volume_control_mixer}', volume set to {self._volume}"
            )
        except Exception as e:
            logger.error(f"Failed to open mixer '{volume_control_mixer}': {e}")

        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

    async def on_set_mute(self, mute: bool = False) -> bool:
        """
        Set mixer mute state.
        """
        self._muted = await self._core.request("dsp.set_mute", mute=mute)
        # if mute is None:
        #     mute = not self._muted

        # if self._mixer is None:
        #     logger.warning("Mixer is not available")
        # else:
        #     try:
        #         self._mixer.setmute(int(mute))
        #         self._muted = self.on_get_mute()
        #     except alsaaudio.ALSAAudioError as exc:
        #         if self._mixer:
        #             if self._muted:
        #                 self._mixer.setvolume(0)
        #             else:
        #                 self._mixer.setvolume(
        #                     self.volume_to_mixer_volume(self._volume)
        #                 )
        #             logger.warning(f"Mute failed using volume settings: {exc}")
        #         else:
        #             logger.error(f"Mute failed: {exc}")

        #     except Exception as exc:
        #         logger.error(
        #             f"Unexpected error while setting mute state or no hardware mute available: {exc}"
        #         )

        self._core.send(
            target=["web", "display", "bluetooth", "infrared", "gpio"],
            event="mixer_mute",
            mute=self._muted,
        )
        logger.info(f"Muted: {self._muted}, Volume: {self._volume}")
        return self._muted

    async def on_get_mute(self) -> Optional[bool]:
        """
        Get mixer mute state.
        """
        # if self._mixer is None:
        #     logger.warning("Mixer is not available")
        # else:
        #     try:
        #         channels_muted = self._mixer.getmute()

        #         if all(channels_muted):
        #             self._muted = True
        #         if not any(channels_muted):
        #             self._muted = False

        #     except alsaaudio.ALSAAudioError as exc:
        #         logger.warning(f"ALSA error while getting mute state: {exc}")
        #     except Exception as exc:
        #         logger.error(
        #             f"Unexpected error while getting mute state or no hardware mute available: {exc}"
        #         )
        self._muted = await self._core.request("dsp.get_mute")
        return self._muted

    async def on_toggle_mute(self) -> bool:
        self._muted = await self._core.request("dsp.toggle_mute")
        self._core.send(
            target=["web", "display", "bluetooth", "infrared", "gpio"],
            event="mixer_mute",
            mute=self._muted,
        )
        logger.info(f"Muted: {self._muted}, Volume: {self._volume}")
        return self._muted

    async def on_get_volume(self) -> Optional[int]:
        """
        Get mixer volume.
        """

        volume_db = await self._core.request("dsp.get_volume")
        self._volume = await self._core.request("dsp.db_to_volume", volume_db=volume_db)

        # if self._mixer is None:
        #     logger.warning("Mixer is not available")
        # else:
        #     try:
        #         channels = self._mixer.getvolume()
        #         if len(channels):
        #             if not self._muted:
        #                 self._volume = self.mixer_volume_to_volume(channels[0])

        #     except alsaaudio.ALSAAudioError as exc:
        #         logger.warning(f"ALSA error while getting volume: {exc}")
        #         return None
        #     except Exception as exc:
        #         logger.error(
        #             f"Unexpected error while getting volume or no hardware volume available: {exc}"
        #         )
        return self._volume

    async def on_set_volume(self, volume: int = 0) -> bool:
        """
        Set Volume
        """
        self._volume = volume
        volume_to_db = await self._core.request("dsp.volume_to_db", volume=volume)

        if self._volume_event_task and not self._volume_event_task.done():
            self._volume_event_task.cancel()

        async def _set_volume(volume: int):
            try:
                await self._core.request("dsp.set_volume", volume_db=volume_to_db)
                # await asyncio.to_thread(
                #     self._mixer.setvolume,
                #     self.volume_to_mixer_volume(volume),
                # )
            except Exception as exc:
                logger.error(f"Failed to set volume: {exc}")

        async def _delayed_volume_event(volume: int):
            try:
                await asyncio.sleep(0.2)
                # if self._mixer is None:
                #     logger.warning("Mixer is not available")

                self._core.send(
                    target=["web", "display", "bluetooth", "infrared", "gpio"],
                    event="volume_changed",
                    volume=self._volume,
                )
            except asyncio.CancelledError:
                pass

        # if self._mixer is not None:
        #     self._core.send(target=["display"], event="volume_changed", volume=volume)
        #     asyncio.create_task(_set_volume(self._volume))
        #     self._db.set_config({"mixer":{"volume_default":self._volume}})

        asyncio.create_task(_set_volume(self._volume))
        self._db.set_config({"mixer": {"volume_default": self._volume}})

        self._volume_event_task = asyncio.create_task(
            _delayed_volume_event(self._volume)
        )
        return self._volume

    async def on_volume_up(self):
        volume = await self.on_get_volume()
        await self.on_set_volume(min(volume + 1, VOL_MAX))

    async def on_volume_down(self):
        volume = await self.on_get_volume()
        await self.on_set_volume(max(volume - 1, VOL_MIN))

    def volume_to_mixer_volume(self, volume):
        if volume == 0:
            return 0
        mixer_volume = VOL_MIN + volume * (VOL_MAX - VOL_MIN) / 100.0
        mixer_volume = 50 * math.log10(mixer_volume)
        return int(mixer_volume)

    def mixer_volume_to_volume(self, mixer_volume):
        volume = mixer_volume
        volume = math.pow(10, volume / 50.0)
        volume = (volume - VOL_MIN) * 100.0 / (VOL_MAX - VOL_MIN)
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

    def on_alsa_devices(self, cmd: str):
        if cmd not in ("arecord", "aplay"):
            raise ValueError("cmd must be 'arecord' or 'aplay'")

        result = subprocess.run([cmd, "-L"], capture_output=True, text=True)
        lines = result.stdout.splitlines()

        devices = [
            {
                "name": "None",
                "device": None,
                "description": None,
            }
        ]
        current_device = None
        description_lines = []

        for line in lines:
            if line and not line.startswith(" "):
                if current_device and current_device.startswith(("hw:", "plughw:")):
                    devices.append(
                        {
                            "name": current_device,
                            "device": current_device,
                            "description": " ".join(description_lines[1:]).strip(),
                        }
                    )

                current_device = line.strip()
                description_lines = []
            else:
                description_lines.append(line.strip())

        if current_device and current_device.startswith(("hw:", "plughw:")):
            devices.append(
                {
                    "name": current_device,
                    "device": current_device,
                    "description": " ".join(description_lines[1:]).strip(),
                }
            )

        return devices

    async def set_mixer(self, mixer: str):
        with open(PLAYBACK_MIXERS_PATH, "r", encoding="utf-8") as f:
            cards = json.load(f)

        for card in cards:
            if card.get("device") == mixer:
                dtoverlay = card.get("dtoverlay") or None
                await self._system.write_dtoverlay("#mixer_overlay", dtoverlay)
