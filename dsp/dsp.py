import yaml
import subprocess
import logging
import asyncio

from camilladsp import CamillaClient, ProcessingState
from core.actor import Actor

logger = logging.getLogger(__name__)

HOST = "127.0.0.1"
PORT = 1234
CONFIG_PATH = "/home/pi/berryaudio/dsp/camilladsp/configs/camilladsp.yml"

VOL_MIN_DB = -80.0
VOL_MAX_DB = 0.0


class DspExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._client = CamillaClient(HOST, PORT)
        self._default_capture_device = self._config.get("dsp", {}).get(
            "default_capture_device"
        )
        self._default_gain = self._config.get("dsp", {}).get("default_gain", 0)
        self._resample_rate = self._config.get("dsp", {}).get("resample_rate", None)

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
        await self.on_set_capture_device()
        await self.on_service("restart")
        logger.info(f"Started")

    async def on_stop(self):
        logger.info("Stopped")

    async def on_event(self, message):
        pass

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
            logger.info("CamillaDSP state triggered %s OK", state)
        except subprocess.CalledProcessError as e:
            logger.error("CamillaDSP state triggered %s failed: %s", state, e.stderr)
            raise ValueError(
                f"CamillaDSP state triggered {state} failed: {e.stderr}"
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

            if sampleformat is not None:
                config["devices"]["capture"]["format"] = sampleformat
            else:
                config["devices"]["capture"].pop("format", None)

            self._write_config(config)
            self._core.send(
                event="dsp_options_before",
                capture_device=capture_device,
                sample_rate=config["devices"]["samplerate"],
            )

            for _ in range(5):
                await asyncio.sleep(1)
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
                        )

                        resample_info = (
                            f" | Capture Rate {new_capture_rate}Hz"
                            if self._resample_rate
                            else ""
                        )
                        info = f"DSP: {capture_device} | Gain {float(gain)}dB | {new_sample_rate}Hz | Format {new_capture_format} | Volume {new_volume}dB | Mute {new_mute}{resample_info}"
                        divider = "-" * len(info)
                        logger.info(divider)
                        logger.info(info)
                        logger.info(divider)

                        return True
                except Exception:
                    logger.debug("Waiting for CamillaDSP to respond...")
            else:
                logger.warning("DSP timed out.Please try again")
                self._core.send(
                    event="dsp_options_changed",
                    capture_device=capture_device,
                    sample_rate=new_sample_rate,
                    sample_format=new_capture_format,
                )
                raise ValueError("DSP timed out.Please try again")

        except Exception as e:
            self._core.send(
                event="error", message="DSP failed to update capture. Please try again"
            )

    def on_status(self):
        self._client.connect()
        config = self._client.config.active()
        self._client.disconnect()
        return config

    def on_volume_to_db(self, volume: int) -> float:
        db = VOL_MIN_DB + (int(volume) / 100) * (VOL_MAX_DB - VOL_MIN_DB)
        return round(db, 1)

    def on_db_to_volume(self, volume_db: float) -> int:
        volume = (volume_db - VOL_MIN_DB) / (VOL_MAX_DB - VOL_MIN_DB) * 100
        return max(0, min(100, round(volume)))

    def on_get_volume(self):
        self._client.connect()
        volume_db = self._client.volume.main_volume()
        self._client.disconnect()
        return volume_db

    def on_set_volume(self, volume_db: float = None):
        self._client.connect()
        self._client.volume.set_main_volume(float(volume_db))
        self._client.disconnect()
        logger.info(f"DSP volume set to: {volume_db} dB")
        return volume_db

    def on_get_mute(self):
        self._client.connect()
        mute = self._client.volume.main_mute()
        self._client.disconnect()
        return mute

    def on_set_mute(self, mute: bool = False):
        self._client.connect()
        self._client.volume.set_main_mute(bool(mute))
        self._client.disconnect()
        logger.info(f"DSP mute set to: {self._muted}")
        return mute

    def on_toggle_mute(self):
        self._client.connect()
        new_mute = self._client.volume.toggle_mute(fader=0)
        self._client.disconnect()
        logger.info(f"DSP mute set to: {new_mute}")
        return new_mute
