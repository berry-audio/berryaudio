import RPi.GPIO as GPIO
import json
import logging

from pathlib import Path
from datetime import datetime
from core.actor import SourceActor
from core.models import Track, Source, Tuner
from core.types import PlaybackControls


logger = logging.getLogger(__name__)

TUNERS_LIST_PATH = Path(__file__).parent.parent / "tuner" / "tuners.json"
PCM1861_MD_GPIO_PIN = 4
SI4703_RESET_GPIO_PIN = 16
SI4703_ADDR = 0x10


class TunerExtension(SourceActor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._db = db
        self._name = name
        self._core = core
        self._config = config
        self._input_device = self._config.get(
            self._name, {}).get("input_device")
        self._output_device = self._config.get(
            "mixer", {}).get("output_device")
        self._sample_rate = self._config.get(
            self._name, {}).get("sample_rate", 44100)
        self._bit_depth = self._config.get(
            self._name, {}).get("bit_depth", "S16_LE")
        self._gain = self._config.get(self._name, {}).get("gain", 0)
        self._hw_device = self._config.get(self._name, {}).get("hw_device")
        self._hw_device_params = None
        self._audio_codec = "PCM"
        self._channels = 2
        self._tuner = None
        self._channel_min = None
        self._channel_max = None
        self._channel_step = None
        self._channel_current = None
        self._track = Tuner(
            uri=self._name,
        )
        self._source = Source(
            name="Tuner",
            uri=self._name,
            controls=[
                PlaybackControls.NEXT,
                PlaybackControls.PREVIOUS,
                PlaybackControls.REPEAT,
                PlaybackControls.SHUFFLE,
            ],
            state={},
        )

    async def on_config_update(self, config):
        updated_config = config[self._name]
        if not updated_config:
            return

        if "hw_device" in updated_config:
            if self._tuner:
                self._tuner.shutdown()
                self._tuner = None
            self._hw_device = updated_config["hw_device"]
            await self._core.request("source.set", uri=None)

        if "input_device" in updated_config:
            self._input_device = updated_config["input_device"]

        if "sample_rate" in updated_config:
            self._sample_rate = updated_config["sample_rate"]

        if "gain" in updated_config:
            self._gain = updated_config["gain"]

        if await self.is_active():
            await self._core.request(
                "dsp.set_capture_device",
                gain=self._gain,
                device=self._input_device,
                samplerate=self._sample_rate,
            )

    async def is_active(self):
        source = await self._core.request("source.get")
        return bool(source and source.uri == self._name)

    async def on_start(self):
        self._init_db()
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        await self.on_stop_service()
        logger.info("Stopped")

    async def on_start_service(self):
        await self._core.request(
            "dsp.set_capture_device",
            gain=self._gain,
            device=self._input_device,
            samplerate=self._sample_rate,
        )
        await self._init_tuner()
        logger.info("Starting service")
        return self._source

    async def on_stop_service(self):
        if self._tuner:
            self._tuner.shutdown()
            self._tuner = None
        self._disable_mux()
        await self._core.request("playback.clear")
        logger.info("Stopping service")
        return True

    def _init_db(self):
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS tuner (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                channel     INTEGER NOT NULL,
                name        TEXT    NOT NULL,
                last_modified TEXT  NOT NULL
            );
            """
        )

    def _read_stats(self):
        self._channel_current = self._tuner.getChannel()
        self._tuner.si4703ReadRegisters()

        is_stereo = (
            self._tuner.si4703_registers[self._tuner.SI4703_STATUSRSSI]
            & (1 << self._tuner.SI4703_STEREO)
        ) != 0
        rssi = self._tuner.si4703_registers[self._tuner.SI4703_STATUSRSSI] & 0xFF

        channels = 2 if is_stereo else 1
        channels_text = "Stereo" if is_stereo else "Mono"
        logger.info(
            f"{self._channel_current:.1f} MHz | {channels_text} | Signal: {rssi:3d}/127")

        return self._channel_current, channels, channels_text, rssi

    async def _status(self):
        """Display current tuner status"""
        freq, channels, channels_text, rssi = self._read_stats()
        track = self._track.copy(
            update={
                "uri": f"{self._name}",
                "name": f"FM {(freq/10):.1f} MHz",
                "channels": channels,
                "channel": freq,
                "sample_rate": self._sample_rate,
                "bit_depth": self._bit_depth,
                "audio_codec": self._audio_codec,
            }
        )
        self._track = track
        await self._core.request("playback.set_metadata", track=self._track)
        self._core.send(
            target=["web", "display"], event="channel_updated", channel=freq
        )

    def _enable_mux(self):
        "Enable PCM1861 Audio Mux for berry audio hat"
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PCM1861_MD_GPIO_PIN, GPIO.OUT)
            GPIO.output(PCM1861_MD_GPIO_PIN, GPIO.LOW)
            logger.debug(
                "Audio mux enabled: GPIO taken LOW PCM1861 specific command"
            )
        except Exception as e:
            logger.error(e)
            raise ValueError(e)

    def _disable_mux(self):
        "Disable PCM1861 Audio Mux for berry audio board hat"
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PCM1861_MD_GPIO_PIN, GPIO.IN)
            logger.debug(
                "Audio mux disabled: GPIO taken HIGH PCM1861 specific command"
            )
        except Exception as e:
            logger.error(e)
            raise ValueError(e)

    async def _init_tuner(self):
        """Detect tuner configurations"""
        self._tuner = None

        if self._hw_device in ('si4703-ba', 'si4703'):
            try:
                from .si4703 import si4703Radio

                self._tuner = si4703Radio(
                    SI4703_ADDR, resetPin=SI4703_RESET_GPIO_PIN)
                self._tuner.init()

                self._hw_device_params = self.on_devices(self._hw_device)
                self._channel_min = self._hw_device_params.get(
                    'channel_min', 875)
                self._channel_max = self._hw_device_params.get(
                    'channel_max', 1080)
                self._channel_step = self._hw_device_params.get(
                    'channel_step', 1)
                
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

                if self._hw_device == 'si4703-ba':
                    self._enable_mux()

                logger.info(self._hw_device)
            except Exception as e:
                self._tuner = None
                logger.error(e)
                raise ValueError(e)
        else:
            self._tuner = None
            logger.error(f"Tuner not found")
            raise ValueError(f"Tuner not found")

        await self.on_set_channel(
            self._channel_current if self._channel_current is not None else self._channel_min
        )

    def _build_tuner(self, row) -> any:
        return {
            "uri": f"{self._name}:{row.id}",
            "name": row.name,
            "channel": row.channel,
            "channels": self._channels,
            "sample_rate": self._sample_rate,
            "bit_depth": self._bit_depth,
            "audio_codec": self._audio_codec,
        }

    def on_directory(
        self,
        uri: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        if not uri:
            raise ValueError(f"No 'uri' was defined.")

        values = uri.split(":")
        values_len = len(values)

        if values_len and values_len == 1:
            base_sql = (
                f"""
                    SELECT 
                        a.*
                    FROM tuner a
                    WHERE %s
                    ORDER BY a.channel ASC
                """
                % "1"
            )
            sql = base_sql.rstrip(";")
            params = []
            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)

                if offset is not None:
                    sql += " OFFSET ?"
                    params.append(offset)

            rows = self._db.fetchall(sql, params)
        return [Tuner(**self._build_tuner(row)) for row in rows]

    async def on_preset_add(self, channel, name=None):
        preset_name = name if name not in (None, "") else f"FM #{channel}"
        cursor = self._db.execute(
            """INSERT INTO tuner (name, channel, last_modified)
            VALUES (?, ?, ?)""",
            (preset_name, channel, datetime.now().isoformat()),
        )
        row = self._db.execute(
            "SELECT * FROM tuner WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        logger.info(f"Tuner preset {preset_name} {channel} saved")
        self._core.send(
            target=["web", "display"], event="preset_saved", item=self._build_tuner(row)
        )
        return True if row else False

    async def on_preset_edit(self, id):
        pass

    async def on_preset_delete(self, id):
        pass

    async def on_get_channel(self):
        if self._tuner:
            return self._tuner.getChannel()
        return False

    async def on_set_channel(self, channel):
        if self._tuner:
            self._tuner.setChannel(channel)
            await self._status()
            return True
        return False

    async def on_seek_up(self, auto=False):
        if not self._tuner:
            raise ValueError("No tuner hardware found")
        if auto:
            self._tuner.seekUp()
        else:
            new_channel = self._channel_current + self._channel_step
            if new_channel > self._channel_max:
                new_channel = self._channel_min
            await self.on_set_channel(new_channel)
        return True

    async def on_seek_down(self, auto=False):
        if not self._tuner:
            raise ValueError("No tuner hardware found")
        if auto:
            self._tuner.seekDown()
        else:
            new_channel = self._channel_current - self._channel_step
            if new_channel < self._channel_min:
                new_channel = self._channel_max
            await self.on_set_channel(new_channel)
        return True

    async def on_playback_uri(self, path: str) -> bool:
        row = self._db.execute(
            "SELECT * FROM tuner WHERE id = ?", (path,)
        ).fetchone()

        if row is None:
            logger.warning(f"Tuner preset not found: {path}")
            return False

        if self._tuner is None:
            logger.warning("Tuner is not initialized")
            return False

        self._track = Tuner(**self._build_tuner(row))
        await self.on_set_channel(int(row["channel"]))
        return self._name

    async def on_lookup_track(self, path: str) -> Track:
        row = self._db.execute(
            "SELECT * FROM tuner WHERE id = ?", (path,)).fetchone()
        return Tuner(**self._build_tuner(row))

    def on_devices(self, device=None):
        with open(TUNERS_LIST_PATH, "r", encoding="utf-8") as f:
            tuners = json.load(f)
        if device is None:
            return tuners
        return next(
            (tuner for tuner in tuners if tuner.get("device") == device),
            None,
        )
