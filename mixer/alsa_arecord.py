import asyncio
import os
import logging

from core.actor import SourceActor
from core.models import Track, TlTrack, Source, RefType
from core.types import PlaybackState

logger = logging.getLogger(__name__)


class AlsaArecord:
    def __init__(
        self,
        core,
        input_device=None,
        output_device=None,
        sample_rate=44100,
        bit_depth="S16_LE",
        channels=2,
        gain=0,
    ):
        self._core = core
        self._input_device = input_device
        self._output_device = output_device
        self._sample_rate = sample_rate
        self._bit_depth = bit_depth
        self._channels = channels
        self._audio_codec = "PCM"
        self._gain = gain
        self._proc_record = None
        self._proc_sox = None
        self._proc_play = None
        self._pipe_fds = []

    async def start_service(self):
        try:
            record_read, record_write = os.pipe()
            sox_read, sox_write = os.pipe()
            self._pipe_fds = [record_read, record_write, sox_read, sox_write]

            if not self._input_device:
                raise ValueError("Input device not assigned")

            if not self._output_device:
                raise ValueError("Output device not assigned")

            arecord_cmd = [
                "arecord",
                "-D",
                self._input_device,
                "-f",
                self._bit_depth,
                "-r",
                str(self._sample_rate),
                "-c",
                str(self._channels),
                "-t",
                "raw",
                "-B",
                "50000",
                "-F",
                "12500",
            ]
            sox_cmd = [
                "sox",
                "-t",
                "raw",
                "-e",
                "signed",
                "-b",
                "32",
                "-r",
                str(self._sample_rate),
                "-c",
                str(self._channels),
                "-",
                "-t",
                "raw",
                "-e",
                "signed",
                "-b",
                "32",
                "-r",
                str(self._sample_rate),
                "-c",
                str(self._channels),
                "-",
                "gain",
                str(self._gain),
            ]
            aplay_cmd = [
                "aplay",
                "-D",
                self._output_device,
                "-f",
                self._bit_depth,
                "-r",
                str(self._sample_rate),
                "-c",
                str(self._channels),
                "-t",
                "raw",
                "-B",
                "50000",
                "-F",
                "12500",
            ]

            # Start arecord
            self._proc_record = await asyncio.create_subprocess_exec(
                *arecord_cmd, stdout=record_write, stderr=asyncio.subprocess.DEVNULL
            )

            # Start sox add Gain
            self._proc_sox = await asyncio.create_subprocess_exec(
                *sox_cmd,
                stdin=record_read,
                stdout=sox_write,
                stderr=asyncio.subprocess.DEVNULL,
            )

            # Start aplay
            self._proc_play = await asyncio.create_subprocess_exec(
                *aplay_cmd, stdin=sox_read, stderr=asyncio.subprocess.DEVNULL
            )

            for fd in self._pipe_fds:
                os.close(fd)
            self._pipe_fds = []

            return (
                True,
                self._sample_rate,
                self._bit_depth,
                self._channels,
                self._audio_codec,
            )

        except Exception as e:
            self._core.send(target=["web", "display"], event="error", message=str(e))
            logger.error(f"Failed to start pipeline: {e}")
            await self.stop_service()
            return False

    async def stop_service(self):
        for fd in self._pipe_fds:
            try:
                os.close(fd)
            except OSError:
                pass
        self._pipe_fds = []

        for proc in (self._proc_play, self._proc_sox, self._proc_record):
            if proc is not None:
                try:
                    proc.terminate()
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    proc.kill()
                except Exception as e:
                    logger.warning(f"Error stopping process: {e}")

        self._proc_record = None
        self._proc_sox = None
        self._proc_play = None
