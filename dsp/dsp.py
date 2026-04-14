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
        self._default_capture_samplerate = (
            44100  # variable rate controlled by incoming audio data
        )
        self._default_samplerate = 192000  # output/resampling rate
        self._muted = False
        self._resample = False

    async def on_config_update(self, config):
        pass

    async def on_start(self):
        await self.on_set_capture_device(
            device=None, gain=None, samplerate=self._default_capture_samplerate
        )
        logger.info(f"Started CamillaDSP with resample set to {self._resample}")

    async def on_stop(self):
        self._client.disconnect()
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
            self._core.send(event="dsp_options_changed")
            logger.info("CamillaDSP state triggered %s OK", state)
        except subprocess.CalledProcessError as e:
            logger.error("CamillaDSP state triggered %s failed: %s", state, e.stderr)
            raise ValueError(
                f"CamillaDSP state triggered {state} failed: {e.stderr}"
            ) from e

    async def on_set_capture_device(
        self, device=None, gain: float = None, samplerate: int = None, sampleformat=None
    ):
        """Update config file directly then restart CamillaDSP."""
        try:
            config = self._read_config()

            current_capture = config["devices"]["capture"]["device"]
            current_gain = config["filters"]["Gain"]["parameters"]["gain"]
            current_samplerate = (
                config["devices"]["capture_samplerate"]
                if self._resample
                else config["devices"]["samplerate"]
            )

            gain = gain if gain else self._default_gain
            capture_device = device if device else self._default_capture_device
            samplerate = samplerate if samplerate else current_samplerate

            if self._resample:
                config["devices"]["samplerate"] = self._default_samplerate
                config["devices"]["resampler"]["type"] = "Synchronous"
                config["devices"]["capture_samplerate"] = samplerate
            else:
                config["devices"].pop("resampler", None)
                config["devices"]["samplerate"] = samplerate

            config["filters"]["Gain"]["parameters"]["gain"] = gain
            config["devices"]["capture"]["device"] = capture_device

            if sampleformat:
                config["devices"]["capture"]["format"] = sampleformat
            else:
                config["devices"]["capture"].pop("format", None)

            self._write_config(config)

            for _ in range(30):
                await asyncio.sleep(0.08)
                try:
                    self._client.connect()
                    self._client.config.set_active(config)
                    state = self._client.general.state()

                    if state == ProcessingState.RUNNING:
                        self._core.send(event="dsp_options_changed")
                        logger.info(
                            f"CamillaDSP capture device '{capture_device}', gain {float(gain)} dB, samplerate {samplerate} Hz, sampleformat {sampleformat}"
                        )
                        self._client.disconnect()
                        return True
                except Exception:
                    logger.debug("Waiting for CamillaDSP to respond...")
            else:
                logger.warning("CamillaDSP timed out.Please try again")
                raise ValueError("CamillaDSP timed out.Please try again")

        except Exception as e:
            logger.error(f"CamillaDSP failed to update {e}. Restarting.")
            await self.on_service("restart")
            raise ValueError("CamillaDSP failed to update capture") from e

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
        logger.info(f"CamillaDSP volume set to: {volume_db} dB")
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
        self._muted = bool(mute)
        logger.info(f"CamillaDSP mute set to: {self._muted}")
        return mute

    def on_toggle_mute(self):
        self._client.connect()
        new_mute = self._client.volume.toggle_mute(fader=0)
        self._client.disconnect()
        self._muted = new_mute
        logger.info(f"CamillaDSP mute set to: {new_mute}")
        return new_mute
