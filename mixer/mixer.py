import logging
import alsaaudio
import math
import asyncio
import json
import re
import subprocess

from pathlib import Path
from typing import Optional

from core.actor import Actor
from core.util.system import SystemUtil


logger = logging.getLogger(__name__)

DTOVERLAY_DICT = Path(__file__).parent.parent / "mixer" / "dtoverlay.json"
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
        self._hw_device = self._config.get("mixer", {}).get("hw_device")
        self._volume = self._config.get("mixer", {}).get("volume_default")
        self._volume_device = self._config.get("mixer", {}).get("volume_device")
        self._dtoverlay = self._config.get("mixer", {}).get("dtoverlay")
        self._muted = False
        self._volume_event_task = None
        self._mixer = None
        self._loop = asyncio.get_running_loop()

    async def on_config_update(self, config):
        updated_config = config[self._name]

        if not updated_config:
            return

        if "hw_device" in updated_config:
            self._hw_device = updated_config.get("hw_device")

        if "volume_device" in updated_config:
            self._volume_device = updated_config.get("volume_device")

        if "dtoverlay" in updated_config:
            self._dtoverlay = updated_config.get("dtoverlay")
            await self._system.write_dtoverlay("#mixer_overlay", self._dtoverlay)

        self._mixer = self.alsa_mixer_setup()
        self._core.send(event="system", action="restart")

    async def on_start(self):
        self._mixer = self.alsa_mixer_setup()
        self._volume = await self.on_get_volume()
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

    async def on_set_mute(self, mute: bool = False) -> bool:
        """Set or toggles mixer mute state"""
        if self._mixer is None:
            self._muted = await self._core.request("dsp.set_mute", mute=mute)
        else:
            self._mixer.setmute(int(mute))
            self._muted = await self.on_get_mute()

        self._core.send(
            target=["web", "display", "bluetooth", "infrared", "gpio"],
            event="mixer_mute",
            mute=self._muted,
        )
        logger.info(f"Muted: {self._muted}")
        return self._muted

    async def on_get_mute(self) -> Optional[bool]:
        """Get mixer mute state"""
        if self._mixer is None:
            self._muted = await self._core.request("dsp.get_mute")
        else:
            channels_muted = self._mixer.getmute()

            if all(channels_muted):
                self._muted = True
            if not any(channels_muted):
                self._muted = False

        return self._muted

    async def on_toggle_mute(self) -> bool:
        mute = not self._muted

        if self._mixer is None:
            self._muted = await self._core.request("dsp.set_mute", mute=mute)
        else:
            self._mixer.setmute(int(mute))
            self._muted = await self.on_get_mute()

        self._core.send(
            target=["web", "display", "bluetooth", "infrared", "gpio"],
            event="mixer_mute",
            mute=self._muted,
        )
        logger.info(f"Muted: {self._muted}")
        return self._muted

    async def on_get_volume(self) -> Optional[int]:
        """Get mixer volume"""
        if self._mixer is None:
            volume_db = await self._core.request("dsp.get_volume")
            self._volume = await self._core.request(
                "dsp.db_to_volume", volume_db=volume_db
            )
            return self._volume

        channels = self._mixer.getvolume()
        self._volume = self.mixer_volume_to_volume(channels[0])
        return self._volume

    async def on_set_volume(self, volume: int = 0) -> bool:
        """Set Mixer Volume"""
        if self._volume_event_task and not self._volume_event_task.done():
            self._volume_event_task.cancel()

        async def set_volume(volume: int):
            self._volume = volume
            if self._mixer is None:
                volume_to_db = await self._core.request(
                    "dsp.volume_to_db", volume=volume
                )
                await self._core.request("dsp.set_volume", volume_db=volume_to_db)
                return

            self._mixer.setvolume(self.volume_to_mixer_volume(volume))

        async def delayed_volume_event(volume: int):
            await asyncio.sleep(0.5)
            self._core.send(
                target=["web", "display", "bluetooth", "infrared", "gpio"],
                event="volume_changed",
                volume=self._volume,
            )

        asyncio.create_task(set_volume(volume))
        self._volume_event_task = asyncio.create_task(
            delayed_volume_event(self._volume)
        )

        self._db.set_config({"mixer": {"volume_default": volume}})
        return self._volume

    async def on_volume_up(self):
        await self.on_set_volume(min(self._volume + 1, VOL_MAX))

    async def on_volume_down(self):
        await self.on_set_volume(max(self._volume - 1, VOL_MIN))

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

    def alsa_mixer_setup(self):
        """Alsa Mixer initial setup"""
        card_controls = self.on_alsa_mixer_volume()
        for control in card_controls:
            if control["name"] == self._volume_device:
                if control["name"] == "Software":
                    logger.info("Volume mixer control: Software (DSP)")
                    return None
                alsamixer = alsaaudio.Mixer(
                    control=control["name"], cardindex=control["index"]
                )
                logger.info(
                    f"Volume mixer control: {control['name']}, card_index={control['index']}"
                )
                return alsamixer

        return None

    def alsa_device_to_card(self, device_name: str) -> str | None:
        """Gets ALSA card name from device"""
        match = re.search(r"CARD=([^,]+)", device_name)
        return match.group(1) if match else None

    def on_alsa_devices(self, cmd: str, filter_loopback: bool = True):
        """Gets ALSA aplay, arecord device list"""
        if cmd not in ("arecord", "aplay"):
            raise ValueError("cmd must be 'arecord' or 'aplay'")
        with open(DTOVERLAY_DICT, "r", encoding="utf-8") as f:
            dtoverlays = json.load(f)
        result = subprocess.run([cmd, "-L"], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        devices = [
            {
                "name": "None",
                "device": None,
                "card": None,
                "dtoverlay": None,
                "description": None,
            }
        ]
        current_device = None
        description_lines = []

        def flush_device():
            if current_device and current_device.startswith(("hw:", "plughw:")):
                card = self.alsa_device_to_card(current_device)
                dtoverlay = dtoverlays.get(card, None)
                devices.append(
                    {
                        "name": current_device,
                        "device": current_device,
                        "card": card,
                        "dtoverlay": dtoverlay,
                        "description": " ".join(description_lines[1:]).strip(),
                    }
                )

        def is_loopback(device: dict) -> bool:
            for field in ("name", "device", "description"):
                value = device.get(field)
                if value and "loopback" in value.lower():
                    return True
            return False

        for line in lines:
            if line and not line.startswith(" "):
                flush_device()
                current_device = line.strip()
                description_lines = []
            else:
                description_lines.append(line.strip())
        flush_device()

        return [d for d in devices if not (filter_loopback and is_loopback(d))]

    def get_alsa_mixers(self):
        try:
            with open("/proc/asound/cards") as f:
                content = f.read()
        except FileNotFoundError:
            raise EnvironmentError("/proc/asound/cards not found. Is ALSA installed?")

        return [
            {
                "index": int(m.group(1)),
                "card": m.group(2).strip(),
                "description": m.group(3).strip(),
            }
            for line in content.splitlines()
            if (m := re.match(r"\s*(\d+)\s+\[(.+?)\].*?:\s*(.+)", line))
        ]

    def get_alsa_volume_controls(self, index=0):
        try:
            result = subprocess.run(
                ["amixer", "-c", str(index), "scontents"],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError:
            raise EnvironmentError(
                "amixer not found. Install: sudo apt install alsa-utils"
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"amixer failed for card {index}: {e.stderr.strip()}")

        controls, current = [], None

        for ls in (l.strip() for l in result.stdout.splitlines()):
            if m := re.match(r"Simple mixer control '(.+?)',(\d+)", ls):
                if current:
                    controls.append(current)
                current = {
                    "name": m.group(1),
                    "index": int(m.group(2)),
                    "type": None,
                    "range": None,
                    "channels": [],
                }

            elif current is None:
                continue

            elif m := re.search(r"Capabilities:(.+)", ls):
                caps = m.group(1).lower()
                current["type"] = (
                    "capture"
                    if "cvolume" in caps
                    else "playback" if "pvolume" in caps else None
                )

            elif m := re.search(
                r"Limits:\s+(?:Playback|Capture)\s+(-?\d+)\s+-\s+(-?\d+)", ls
            ):
                current["range"] = {"min": int(m.group(1)), "max": int(m.group(2))}

            elif m := re.match(
                r"(.+?):\s+(?:Playback|Capture)\s+-?\d+\s+\[(\d+)%\](?:\s+\[-?[\d.]+dB\])?(?:\s+\[(on|off)\])?",
                ls,
            ):
                current["channels"].append(
                    {
                        "channel": m.group(1).strip(),
                        "percent": int(m.group(2)),
                        "muted": (m.group(3) == "off") if m.group(3) else None,
                    }
                )

        if current:
            controls.append(current)
        return controls

    def on_alsa_mixer_volume(self, card: str = None):
        software_control = {
            "name": "Software",
            "description": "Software volume from DSP",
            "index": None,
            "type": "playback",
            "channels": 2,
            "range": {"min": -100, "max": 0, "unit": "dB"},
            "muted": False,
        }

        if card is None:
            if self._hw_device is not None:
                card = self.alsa_device_to_card(self._hw_device)
            else:
                return [software_control]

        cards = self.get_alsa_mixers()
        matched = next(
            (
                c
                for c in cards
                if card.lower() in c["card"].lower()
                or card.lower() in c["description"].lower()
            ),
            None,
        )

        if not matched:
            raise ValueError(f"No card matching '{card}' found.")

        controls = [
            {
                "name": c["name"],
                "description": matched["description"],
                "index": matched["index"],
                "type": c["type"],
                "channels": len(c["channels"]),
                "range": {**c["range"], "unit": "steps"},
                **(
                    {
                        "muted": any(
                            ch["muted"]
                            for ch in c["channels"]
                            if ch["muted"] is not None
                        )
                    }
                    if any(ch["muted"] is not None for ch in c["channels"])
                    else {}
                ),
            }
            for c in self.get_alsa_volume_controls(matched["index"])
            if c["type"]
            and c["channels"]
            and c["range"]
            and (c["range"]["max"] - c["range"]["min"]) > 1
        ]

        controls.insert(0, software_control)
        return controls
