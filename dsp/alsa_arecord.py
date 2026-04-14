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

    def _get_bit_depth_int(self):
        """Extract numeric bit depth from ALSA format string e.g. S16_LE -> 16"""
        import re

        m = re.search(r"\d+", self._bit_depth)
        return int(m.group()) if m else 16

    

    async def start_service(self):
        try:
            if not self._input_device:
                raise ValueError("Input device not assigned")
            if not self._output_device:
                raise ValueError("Output device not assigned")

            # period_frames = 512
            # period_us = int((period_frames / self._sample_rate) * 1_000_000)

            # alsaloop_cmd = [
            #     "alsaloop",
            #     "-C", self._input_device,
            #     "-P", self._output_device,
            #     "-r", str(self._sample_rate),
            #     "-f", self._bit_depth,
            #     "-c", str(self._channels),
            #     "-s", str(period_frames),
            #     "-t", str(period_us),
            #     "-A", "1",
            #     "-T", "0",
            #     "-v",   # verbose
            # ]

            

            # logger.debug(f"alsaloop cmd: {' '.join(alsaloop_cmd)}")

            # self._proc_loop = await asyncio.create_subprocess_exec(
            #     *alsaloop_cmd,
            #     stderr=asyncio.subprocess.PIPE,
            #     stdout=asyncio.subprocess.DEVNULL,
            # )

            # async def log_stderr():
            #     async for line in self._proc_loop.stderr:
            #         decoded = line.decode().strip()
            #         if decoded:
            #             logger.debug(f"alsaloop: {decoded}")

            # asyncio.create_task(log_stderr())

            return (True, self._sample_rate, self._bit_depth, self._channels, self._audio_codec)

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
