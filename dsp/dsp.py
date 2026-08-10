import yaml
import subprocess
import math
import re
import time
import logging
import asyncio

from pathlib import Path
from camilladsp import CamillaClient, ProcessingState
from core.actor import Actor
from core.util.system import SystemUtil

logger = logging.getLogger(__name__)

HOST = "127.0.0.1"
PORT = 1234

CONFIG_PATH = Path(__file__).parent / "camilladsp" / "configs" / "camilladsp.yml"

VOL_MIN_DB = -100.0
VOL_MAX_DB = 0.0
VOL_CURVE = 3.0  # higher = more gradual at low end, try 2.0-4.0


class DspExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._system = SystemUtil(core, db)
        self._client = CamillaClient(HOST, PORT)
        self._default_capture_device = self._config.get("dsp", {}).get(
            "default_capture_device"
        )
        self._default_gain = self._config.get("dsp", {}).get("default_gain", 0)
        self._resample_rate = self._config.get("dsp", {}).get("resample_rate", None)
        self._disconnect_task = None

    async def on_config_update(self, config):
        updated_config = config[self._name]
        if not updated_config:
            return

        if "default_gain" in updated_config:
            self._default_gain = updated_config["default_gain"]

        if "resample_rate" in updated_config:
            self._resample_rate = updated_config["resample_rate"]

        await self.on_set_capture_device()

    async def on_start(self):
        await self._system.write_asoundrc(pcm=self._config.get("mixer", {}).get("hw_device"))
        await self.on_set_capture_device()
        await self.on_service("restart")
        logger.info(f"Started")

    async def on_stop(self):
        logger.info("Stopped")

    async def on_event(self, message):
        if (message.get("event") == "system_power_state_changed" and 
            message.get("state") == "standby"):
            
            await self.on_set_capture_device(
                device=self._default_capture_device,
                gain=self._default_gain,
                samplerate=self._resample_rate,
            )

    def _read_config(self):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to read config file: {e}")
            raise ValueError("Failed to read config file") from e

    def _write_config(self, config):
        try:
            with open(CONFIG_PATH, "w") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.error(f"Failed to write config file: {e}")
            raise ValueError("Failed to write config file") from e

    async def on_service(self, state: str):
        """Control CamillaDSP service"""
        try:
            subprocess.run(
                ["sudo", "/bin/systemctl", state, "camilladsp.service"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.info("Service %s OK", state)
        except subprocess.CalledProcessError as e:
            logger.error("Service %s failed: %s", state, e.stderr)
            raise ValueError(
                f"Service {state} failed: {e.stderr}"
            ) from e

    async def on_set_capture_device(
        self,
        device=None,
        gain: float = None,
        samplerate: int = 44100,
        sampleformat=None,
    ):
        """Update config file directly then restart CamillaDSP."""
        try:
            config = self._read_config()

            gain = gain if gain else self._default_gain
            capture_device = device if device else self._default_capture_device
            config["filters"]["Gain"]["parameters"]["gain"] = gain
            config["devices"]["capture"]["device"] = capture_device

            if self._resample_rate is not None:
                config["devices"]["samplerate"] = self._resample_rate
                config["devices"].setdefault("resampler", {})["type"] = "Synchronous"
                config["devices"]["capture_samplerate"] = samplerate
            else:
                config["devices"].pop("resampler", None)
                if samplerate is not None:
                    config["devices"]["samplerate"] = samplerate

            new_capture_format = None
            if sampleformat is not None:
                config["devices"]["capture"]["format"] = sampleformat
                new_capture_format = sampleformat
            else:
                config["devices"]["capture"].pop("format", None)

            self._write_config(config)
            self._core.send(
                event="dsp_options_before",
                capture_device=capture_device,
                sample_rate=config["devices"]["samplerate"],
                resample=self._resample_rate is not None
            )

            new_sample_rate = config["devices"]["samplerate"] or samplerate

            try:
                self._client.connect()
                self._client.config.set_active(config)
                state = self._client.general.state()

                if state == ProcessingState.RUNNING:
                    self._client.general.reload()
                    await asyncio.sleep(0.1)
                    active = self._client.config.active()
                    new_volume = self._client.volume.main_volume()
                    new_mute = self._client.volume.main_mute()

                    new_sample_rate = active["devices"]["samplerate"]
                    new_capture_rate = active["devices"]["capture_samplerate"]
                    new_capture_format = (
                        active["devices"]["capture"]["format"] or "Auto"
                    )

                    self._core.send(
                        event="dsp_options_changed",
                        capture_device=capture_device,
                        sample_rate=new_sample_rate,
                        sample_format=new_capture_format,
                        resample=self._resample_rate is not None
                    )

                    capture_info = (
                        f"{new_capture_rate}Hz"
                        if self._resample_rate
                        else f"{new_sample_rate}Hz"
                    )

                    resample_info = (
                        f"{self._resample_rate}Hz"
                        if self._resample_rate
                        else False
                    )

                    info = f"DSP: {capture_device} | Gain {float(gain)}dB | Actual Rate {capture_info} | Resample {resample_info} | Format {new_capture_format} | Volume {new_volume}dB | Mute {new_mute}"
                    divider = "-" * len(info)
                    logger.info(divider)
                    logger.info(info)
                    logger.info(divider)

                    return True
            except Exception as e:
                logger.warning(e)
                logger.warning("DSP failed to update capture. Trying again...")
                self._core.send(
                    event="dsp_options_error",
                    capture_device=capture_device,
                    sample_rate=new_sample_rate,
                    sample_format=new_capture_format,
                )

        except Exception as e:
            logger.warning(e)
            logger.warning("DSP failed to update capture. Please try again")
            self._core.send(
                event="dsp_options_error",
                capture_device=capture_device,
                sample_rate=new_sample_rate,
                sample_format=new_capture_format,
            )
            self._core.send(
                event="error", message="DSP failed to update capture. Please try again"
            )

    def on_status(self):
        self._client.connect()
        config = self._client.config.active()
        self._client.disconnect()
        return config

    def on_volume_to_db(self, volume: int) -> float:
        if volume <= 0:
            return float(VOL_MIN_DB)
        curved = (volume / 100) ** VOL_CURVE
        min_linear = 10 ** (VOL_MIN_DB / 20)
        max_linear = 10 ** (VOL_MAX_DB / 20)
        linear = min_linear + curved * (max_linear - min_linear)
        db = 20 * math.log10(linear)
        return round(max(VOL_MIN_DB, min(VOL_MAX_DB, db)), 1)

    def on_db_to_volume(self, volume_db: float) -> int:
        if volume_db <= VOL_MIN_DB:
            return 0
        min_linear = 10 ** (VOL_MIN_DB / 20)
        max_linear = 10 ** (VOL_MAX_DB / 20)
        linear = 10 ** (volume_db / 20)
        curved = (linear - min_linear) / (max_linear - min_linear)
        volume = (curved ** (1 / VOL_CURVE)) * 100
        return max(0, min(100, round(volume)))

    def on_get_volume(self):
        self._client.connect()
        volume_db = self._client.volume.main_volume()
        self._client.disconnect()
        return volume_db

    def on_set_volume(self, volume_db: float = None):
        self._client.connect()
        self._client.volume.set_main_volume(float(volume_db))

        if self._disconnect_task and not self._disconnect_task.done():
            self._disconnect_task.cancel()

        async def _delayed_disconnect():
            try:
                await asyncio.sleep(0.3)
                logger.info(f"DSP volume set to: {volume_db} dB")
                self._client.disconnect()
                logger.debug("DSP client disconnected")
            except asyncio.CancelledError:
                pass

        self._disconnect_task = asyncio.create_task(_delayed_disconnect())
        return volume_db

    def on_get_mute(self):
        self._client.connect()
        mute = self._client.volume.main_mute()
        self._client.disconnect()
        return mute

    def on_set_mute(self, mute: bool = False):
        self._client.connect()
        self._client.volume.set_main_mute(mute)
        self._client.disconnect()
        logger.info(f"DSP mute set to: {mute}")
        return mute

    def on_toggle_mute(self):
        self._client.connect()
        new_mute = self._client.volume.toggle_mute(fader=0)
        self._client.disconnect()
        logger.info(f"DSP mute set to: {new_mute}")
        return new_mute