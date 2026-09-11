import yaml
import subprocess
import math
import logging
import functools
import asyncio

from pathlib import Path
from camilladsp import CamillaClient, ProcessingState
from core.actor import Actor
from core.util.system import SystemUtil

logger = logging.getLogger(__name__)

HOST = "127.0.0.1"
PORT = 1234

CONFIG_PATH = Path(__file__).parent / "camilladsp" / \
    "configs" / "camilladsp.yml"

VOL_MIN_DB = -100.0
VOL_MAX_DB = 0.0
VOL_CURVE = 3.0  # higher = more gradual at low end, try 2.0-4.0
CAMILLADSP_PATH = "/usr/local/bin/camilladsp"


class DspExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._system = SystemUtil(core, db)
        self._default_capture_device = self._config.get("dsp", {}).get("default_capture_device")
        self._default_gain = self._config.get("dsp", {}).get("default_gain", 0)
        self._resample_rate = self._config.get("dsp", {}).get("resample_rate", None)
        self._default_sample_rate = 44100
        self._default_sample_format = 'S32_LE'
        self._disconnect_task = None
        self._client = None

    @staticmethod
    def client_connection(func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                if self._client is None:
                    self._client_connect()
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    logger.error(f"Connection failed ({e}), reconnecting...")
                    self._client_connect()
                    return await func(self, *args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                if self._client is None:
                    self._client_connect()
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    logger.error(f"Connection failed ({e}), reconnecting...")
                    self._client_connect()
                    return func(self, *args, **kwargs)
            return sync_wrapper

    def _client_connect(self):
        try:
            self._client = CamillaClient(HOST, PORT)
            self._client.connect()
            logger.info(f"Connected to CamillaDsp on {HOST} {PORT}")
        except Exception as e:
            self._stop_camilladsp()
            logger.error(e)
            raise
            
    async def on_config_update(self, config):
        updated_config = config[self._name]
        if not updated_config:
            return

        if "default_gain" in updated_config:
            self._default_gain = updated_config["default_gain"]
            await self.on_set_capture_gain()

        if "resample_rate" in updated_config:
            self._resample_rate = updated_config["resample_rate"]
            self._core.send(event="system", action="restart")

    async def on_service(self, state: str):
        """Control CamillaDSP service"""
        self._stop_camilladsp()
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
        self._client_connect()

    async def on_start(self):
        await self._system.write_asoundrc(pcm=self._config.get("mixer", {}).get("hw_device"))
        await self.on_set_capture_device()
        logger.info(f"Started")

    async def on_stop(self):
        self._stop_camilladsp()
        logger.info("Stopped")

    def _stop_camilladsp(self):
        try:
            if self._client is not None:
                self._client.disconnect()
        except Exception as e:
            logger.error(e)
        self._client = None
        logger.info(f"CamillaDSP stopped")

    async def on_event(self, message):
        if (message.get("event") == "system_power_state_changed" and
                message.get("state") == "standby"):
            await self.on_set_capture_device(
                device=self._default_capture_device,
                gain=self._default_gain,
                samplerate=self._default_sample_rate,
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
                yaml.dump(config, f, default_flow_style=False,
                          allow_unicode=True)
            logger.info('DSP config written')
        except Exception as e:
            logger.error(f"Failed to write config file: {e}")
            raise ValueError("Failed to write config file") from e

    def _client_connect(self):
        if self._client is not None:
            try:
                self._client.volume.main_volume()
            except Exception as e:
                self._stop_camilladsp()

        if self._client is None:
            try:
                self._client = CamillaClient(HOST, PORT)
                self._client.connect()
                logger.info(f"Connected to CamillaDsp on {HOST} {PORT}")
            except Exception as e:
                self._stop_camilladsp()
                logger.error(e)
            
    @client_connection
    async def on_set_capture_gain(self, gain=None):
        config = self._read_config()
        gain = gain if gain is not None else self._default_gain
        config["filters"]["Gain"]["parameters"]["gain"] = gain
        self._write_config(config)
        self._client.config.set_active(config)
        self._client.general.reload()
        logger.info(f"Capture device gain updated to {gain}")

    async def on_set_capture_device(
        self,
        device: str = None,
        gain: float = None,
        samplerate: int = None,
        sampleformat=None,
        ext: str = None,
    ):
        """Update config file directly then restart CamillaDSP."""
        if self._resample_rate is None:
            await self._core.request("multiroom.stop_snapserver")

        # Set Gain and Capture Device
        config = self._read_config()
        gain = gain if gain is not None else self._default_gain
        samplerate = samplerate if samplerate is not None else self._default_sample_rate
        capture_device = device if device is not None else self._default_capture_device

        config["filters"]["Gain"]["parameters"]["gain"] = gain
        config["devices"]["capture"]["device"] = capture_device

        # Set Samplerate
        if self._resample_rate is not None:
            config["devices"]["samplerate"] = self._resample_rate
            config["devices"]["capture_samplerate"] = samplerate
            config["devices"].setdefault("resampler", {})[
                "type"] = "Synchronous"
        else:
            config["devices"].pop("resampler", None)
            config["devices"]["samplerate"] = samplerate

        # Set Format
        if sampleformat is not None:
            config["devices"]["capture"]["format"] = sampleformat
        else:
            config["devices"]["capture"].pop("format", None)

        self._write_config(config)

        try:
            self._client_connect()
            self._client.config.set_active(config)
            self._client.general.reload()

            for attempt in range(10):
                if self._client.general.state() == ProcessingState.RUNNING:
                    break
                logger.info(f'Waiting for state Running... ({attempt + 1}/10)')
                await asyncio.sleep(0.5)
            else:
                await self._core.request("multiroom.stop_snapserver")
                self._core.send(
                    event="dsp_options_error",
                    message="DSP failed to start.Try again.",
                )
                self._core.send(
                    event="error",
                    message=f"DSP failed to start.Try again.",
                )
                self._stop_camilladsp()

            new_volume = self._client.volume.main_volume()
            new_mute = self._client.volume.main_mute()

            self._core.send(
                event="dsp_options_changed",
                capture_device=capture_device,
                sample_rate=self._resample_rate if self._resample_rate else samplerate,
                sample_format=sampleformat or self._default_sample_format,
                resample=self._resample_rate is not None
            )

            self._core.send(
                event="dsp_state_changed",
                config=config,
            )

            resample_info = (
                f"{self._resample_rate}Hz"
                if self._resample_rate
                else False
            )

            info = (
                f'DSP: {capture_device} | Gain {float(gain)}dB | '
                f'Actual Rate {self._resample_rate if self._resample_rate else samplerate}Hz | Resample {resample_info} | '
                f'Format {sampleformat or "Auto (S32_LE)"} | '
                f'Volume {new_volume}dB | Mute {new_mute}'
            )
            divider = "-" * len(info)
            logger.info(divider)
            logger.info(info)
            logger.info(divider)

            await self._core.request(
                "multiroom.start_snapserver",
                sample_rate=self._resample_rate if self._resample_rate else samplerate,
                bit_depth=sampleformat or self._default_sample_format
            )

            if ext is not None:
                await self._core.request(f"{ext}.start_stream")

        except Exception as e:
            logger.error(e)
            await self._core.request("multiroom.stop_snapserver")
            self._core.send(
                event="dsp_options_error",
                message="DSP failed to start.Try again.",
            )
            self._core.send(
                event="error",
                message=f"DSP failed to start:{e}",
            )
            self._stop_camilladsp()

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

    @client_connection
    def on_get_volume(self):
        volume_db = self._client.volume.main_volume()
        return volume_db

    @client_connection
    def on_set_volume(self, volume_db: float = None):
        self._client.volume.set_main_volume(float(volume_db))
        if self._disconnect_task and not self._disconnect_task.done():
            self._disconnect_task.cancel()

        async def _delayed_disconnect():
            try:
                await asyncio.sleep(0.3)
                logger.info(f"DSP volume set to: {volume_db} dB")
                logger.debug("DSP client disconnected")
            except asyncio.CancelledError:
                pass

        self._disconnect_task = asyncio.create_task(_delayed_disconnect())
        return volume_db

    @client_connection
    def on_get_mute(self):
        mute = self._client.volume.main_mute()
        return mute

    @client_connection
    def on_set_mute(self, mute: bool = False):
        self._client.volume.set_main_mute(mute)
        logger.info(f"DSP mute set to: {mute}")
        return mute

    @client_connection
    def on_toggle_mute(self):
        new_mute = self._client.volume.toggle_mute(fader=0)
        logger.info(f"DSP mute set to: {new_mute}")
        return new_mute

    @client_connection
    def on_signal_levels(self):
        def _build_levels():
            return {
                "levels": self._client.levels.levels(),
                "labels": self._client.levels.labels(),
            }
        try:
            return _build_levels()
        except IOError:
            pass

    @client_connection
    def on_status(self):
        def _build_stats():
            return {
                "capturerate": self._client.rate.capture(),
                "rateadjust": self._client.status.rate_adjust(),
                "bufferlevel": self._client.status.buffer_level(),
                "clippedsamples": self._client.status.clipped_samples(),
                "processingload": self._client.status.processing_load(),
                "resamplerload": self._client.status.resampler_load(),
            }
        try:
            return _build_stats()
        except IOError:
            return _build_stats()

    @client_connection
    def on_get_config(self):
        config = self._client.config.active()
        return config

    @client_connection
    def on_set_config(self, config):
        self._client.config.set_active(config)
        response = self._write_config(config)
        self._core.send(
            event="dsp_state_changed",
            config=self.on_get_config(),
        )
        return response
