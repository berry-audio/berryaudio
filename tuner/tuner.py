import RPi.GPIO as GPIO
import asyncio
import logging

from datetime import datetime
from .si4703 import si4703Radio
from core.actor import SourceActor
from core.models import Track, Source, RefType, Artist, Ref
from core.types import PlaybackControls


logger = logging.getLogger(__name__)

FM_MIN = 875
FM_MAX = 1080
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
        self._input_device = self._config.get("tuner", {}).get("input_device")
        self._output_device = self._config.get("mixer", {}).get("output_device")
        self._sample_rate = self._config.get("tuner", {}).get("sample_rate", 44100)
        self._bit_depth = self._config.get("tuner", {}).get("bit_depth", "S16_LE")
        self._default_channel = self._config.get("tuner", {}).get(
            "default_channel", 875
        )
        self._audio_codec = "PCM"
        self._gain = self._config.get("tuner", {}).get("gain", 0)
        self._channels = 2
        self._tuner = None
        self._track = Track(
            uri=self._name,
            name="Tuner",
            sample_rate=self._sample_rate,
            bit_depth=self._bit_depth,
            channels=self._channels,
            audio_codec=self._audio_codec,
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

        if "input_device" in updated_config:
            self._input_device = updated_config["input_device"]

        if "sample_rate" in updated_config:
            self._sample_rate = updated_config["sample_rate"]

        if "gain" in updated_config:
            self._gain = updated_config["gain"]

        if await self.is_active():
            await self._core.request(
                "dsp.set_capture_device",
                device=self._input_device,
                gain=self._gain,
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
        await self._shutdown_tuner()
        logger.info("Stopped")

    async def on_start_service(self):
        await self._core.request(
            "dsp.set_capture_device",
            gain=self._gain,
            device=self._input_device,
            samplerate=self._sample_rate,
        )
        await self._init_tuner()

        logger.info("Started service")
        return self._source

    async def on_stop_service(self):
        await self._shutdown_tuner()
        await self._core.request("playback.clear")
        logger.debug("Stopped service")
        return True

    def _read_stats(self):
        self._default_channel = self._tuner.si4703GetChannel()
        freq = self._default_channel / 10.0

        self._tuner.si4703ReadRegisters()
        is_stereo = (
            self._tuner.si4703_registers[self._tuner.SI4703_STATUSRSSI]
            & (1 << self._tuner.SI4703_STEREO)
        ) != 0
        rssi = self._tuner.si4703_registers[self._tuner.SI4703_STATUSRSSI] & 0xFF

        channels = 2 if is_stereo else 1
        channels_text = "Stereo" if is_stereo else "Mono"
        logger.info(f"{freq:.1f} MHz | {channels_text} | Signal: {rssi:3d}/127")

        return freq, channels, channels_text, rssi

    async def _status(self):
        """Display current tuner status"""
        freq, channels, channels_text, rssi = self._read_stats()

        track = self._track.copy(
            update={
                "uri": f"{self._name}",
                "name": f"FM {freq:.1f} MHz",
                "channels": channels,
                "artists": frozenset(),
            }
        )
        self._track = track
        await self._core.request("playback.set_metadata", track=self._track)

    def _init_db(self):
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS tuner (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                frequency   INTEGER NOT NULL,
                name        TEXT    NOT NULL,
                views       INTEGER NOT NULL DEFAULT 0,
                last_modified TEXT  NOT NULL
            );
            """
        )

    async def _init_tuner(self):
        """Initialize PCM1861 audio mux and Si4703 FM tuner."""
        # --- Si4703 Reset & Init ---
        try:
            self._tuner = si4703Radio(SI4703_ADDR, resetPin=SI4703_RESET_GPIO_PIN)
            self._tuner.si4703Init()
            await asyncio.sleep(0.1)
            logger.debug("SI4703 tuner enabled")
        except OSError as e:
            logger.error(
                f"Si4703 I2C init failed (check wiring/address 0x{SI4703_ADDR:02X}): {e}"
            )
            self._tuner = None
            raise ValueError(
                f"Si4703 I2C init failed (check wiring/address 0x{SI4703_ADDR:02X}): {e}"
            )
        except Exception as e:
            logger.error(f"Si4703 init unexpected error: {e}")
            self._tuner = None
            raise ValueError(f"Si4703 init unexpected error: {e}")

        if self._tuner:
            # --- Register Configuration ---
            try:
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
            except OSError as e:
                logger.error(f"Si4703 register read/write failed: {e}")
            except (AttributeError, IndexError) as e:
                logger.error(f"Si4703 register mapping error — check constants: {e}")
            except Exception as e:
                logger.error(f"Si4703 configuration unexpected error: {e}")

            # --- Tune to Default Channel ---
            try:
                if self._tuner:
                    self._tuner.si4703SetChannel(self._default_channel)
                    await self._status()
                    logger.debug(
                        f"SI4703 tuned to default channel: {self._default_channel}"
                    )
            except OSError as e:
                logger.error(
                    f"Si4703 failed to tune to channel {self._default_channel}: {e}"
                )
            except Exception as e:
                logger.error(f"Unexpected error tuning to default channel: {e}")

            # --- PCM1861 Audio Mux ---
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(PCM1861_MD_GPIO_PIN, GPIO.OUT)
                GPIO.output(PCM1861_MD_GPIO_PIN, GPIO.LOW)
                logger.debug(
                    "Audio mux enabled: GPIO taken LOW PCM1861 specific command"
                )
            except Exception as e:
                logger.error(f"PCM1861 GPIO setup failed: {e}")

    async def _shutdown_tuner(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PCM1861_MD_GPIO_PIN, GPIO.IN)
        if self._tuner:
            self._tuner.si4703ShutDown()

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
                    ORDER BY a.frequency ASC
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

            def _build_ref(row):
                return {
                    "uri": f"{self._name}:{row.id}",
                    "name": row.name,
                    "artists": frozenset([Artist(name=f"{row.frequency / 10} Mhz")]),
                    "type": RefType.TRACK,
                }

        return [Ref(**_build_ref(row)) for row in rows]

    async def on_create(self, frequency, name=None):
        last_modified = datetime.now().isoformat()
        preset_name = name if name not in (None, "") else f"FM #{frequency}"
        cursor = self._db.execute(
            """INSERT INTO tuner (name, frequency, views, last_modified)
            VALUES (?, ?, ?, ?)""",
            (preset_name, frequency, 0, last_modified),
        )
        row = self._db.execute(
            "SELECT * FROM tuner WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        logger.info(f"Tuner preset {preset_name} {frequency} created")
        self._core.send(
            target=["web", "display"], event="tuner_preset_created", row=dict(row)
        )
        return dict(row) if row else None

    async def on_edit(self, id):
        pass

    async def on_delete(self, id):
        pass

    async def on_get_channel(self):
        if self._tuner:
            return self._tuner.si4703GetChannel()

    async def on_set_channel(self, channel):
        if self._tuner and channel:
            self._tuner.si4703SetChannel(channel)
            await self._status()
        return self._tuner.si4703GetChannel()

    async def on_seek_up(self, auto=False):
        if not self._tuner:
            raise ValueError("No hardware tuner found")
        if auto:
            self._tuner.si4703SeekUp()
        else:
            new_channel = self._default_channel + 1
            if new_channel > FM_MAX:
                new_channel = FM_MIN
            self._tuner.si4703SetChannel(new_channel)
        self._default_channel = new_channel
        await self._status()
        return True

    async def on_seek_down(self, auto=False):
        if not self._tuner:
            raise ValueError("No hardware tuner found")
        if auto:
            self._tuner.si4703SeekDown()
        else:
            new_channel = self._default_channel - 1
            if new_channel < FM_MIN:
                new_channel = FM_MAX
            self._tuner.si4703SetChannel(new_channel)
        self._default_channel = new_channel
        await self._status()
        return True

    def _build_track(self, row) -> any:
        return {
            "uri": f"{self._name}:{row.id}",
            "name": row.name,
            "artists": frozenset([Artist(name=f"{row.frequency / 10} Mhz")]),
            "channels": self._track.channels,
            "sample_rate": self._track.sample_rate,
            "bit_depth": self._track.bit_depth,
            "audio_codec": self._track.audio_codec,
        }

    async def on_playback_uri(self, path: str) -> bool:
        row = self._db.execute("SELECT * FROM tuner WHERE id = ?", (path,)).fetchone()
        if row is None:
            logger.warning(f"Tuner preset not found: {path}")
            return False

        if self._tuner:
            self._tuner.si4703SetChannel(int(row["frequency"]))
            self._default_channel = self._tuner.si4703GetChannel()
            self._track = Track(**self._build_track(row))

            freq, channels, channels_text, rssi = self._read_stats()
            track = self._track.copy(
                update={
                    "channels": int(channels),
                }
            )
            self._track = track
            await self._core.request("playback.set_metadata", track=self._track)

        return self._name

    async def on_lookup_track(self, path: str) -> Track:
        row = self._db.execute("SELECT * FROM tuner WHERE id = ?", (path,)).fetchone()
        return Track(**self._build_track(row))
