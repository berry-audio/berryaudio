import asyncio
import logging
import aiohttp_cors
import threading
import subprocess
import os

from fractions import Fraction
from aiohttp import web, WSMsgType
from core.actor import Actor
from main import USE_GBULB
from core.actor import Actor
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
    RTCIceServer,
    AudioStreamTrack,
)
from av import AudioFrame

logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

ICE_SERVERS = [RTCIceServer(urls="stun:stun.l.google.com:19302")]
ALSA_DEVICE = "plughw:Loopback,1,3"
SAMPLE_RATE = 48000
CHANNELS = 2
SAMPLES_PER_FRAME = 960


class WebRtcExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._current_pc = None
        self._server_stop = asyncio.Event()

    def _run_server_thread(self):
        policy = asyncio.DefaultEventLoopPolicy()
        try:
            os.sched_setscheduler(0, os.SCHED_FIFO, os.sched_param(10))
        except PermissionError:
            logger.warning("Could not set realtime priority (need CAP_SYS_NICE or root)")
        
        loop = policy.new_event_loop()
        asyncio.set_event_loop(loop)
        self._server_stop = asyncio.Event()
        loop.run_until_complete(self.run_server())
        
    async def on_start(self):
        logger.info("Started")
        self._clients = set()
        threading.Thread(target=self._run_server_thread, daemon=True).start()

    async def run_server(self):
        host = "0.0.0.0"
        port = 8082
        self._app = web.Application()

        stream_route = self._app.router.add_post(
            "/stream", self.webrtc_handler)
        cors = aiohttp_cors.setup(self._app, defaults={"*": aiohttp_cors.ResourceOptions(
            allow_credentials=True, expose_headers="*", allow_headers="*")})
        cors.add(stream_route)

        runner = web.AppRunner(self._app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"WebRTC Server running at http://{host}:{port}")

        await self._server_stop.wait()
        await runner.cleanup()

    async def _close_current_webrtc_connection(self):
        if self._current_pc is not None:
            await self._current_pc.close()
            self._current_pc = None

    async def webrtc_handler(self, request):
        logging.getLogger("aiortc.rtcrtpsender").setLevel(logging.WARNING)

        params = await request.json()
        offer_desc = RTCSessionDescription(
            sdp=params["sdp"], type=params["type"])

        await self._close_current_webrtc_connection()

        pc = RTCPeerConnection(
            configuration=RTCConfiguration(iceServers=ICE_SERVERS))
        self._current_pc = pc

        track = LoopbackAudioTrack()

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info("Connection state is %s", pc.connectionState)
            if pc.connectionState in ("failed", "closed", "disconnected"):
                track.stop()
                await pc.close()
                if self._current_pc is pc:
                    self._current_pc = None

        await pc.setRemoteDescription(offer_desc)
        pc.addTrack(track)

        for transceiver in pc.getTransceivers():
            if transceiver.kind == "audio":
                transceiver.direction = "sendonly"

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.json_response({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})

    async def on_event(self, message):
        pass

    async def on_stop(self):
        await self._close_current_webrtc_connection()
        
        self.running = False
        if hasattr(self, "_server_stop"):
            self._server_stop.set()
        if hasattr(self, "_server_task"):
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped")


class LoopbackAudioTrack(AudioStreamTrack):
    kind = "audio"

    def __init__(self):
        super().__init__()
        self.timestamp = 0
        self.process = None
        self.running = False       

    async def _log_stderr(self):
        assert self.process is not None
        async for line in self.process.stderr:
            logger.warning("arecord: %s", line.decode(errors="replace").rstrip())
    
    def _read_exact(self, n):
        buf = bytearray()
        while len(buf) < n:
            chunk = self.process.stdout.read(n - len(buf))
            if not chunk:
                raise EOFError("arecord stream ended")
            buf.extend(chunk)
        return bytes(buf)

    async def recv(self):
        if self.process is None:
            self.running = True
            self.process = subprocess.Popen(
                [
                    "arecord", "-D", ALSA_DEVICE,
                    "-f", "S16_LE",
                    "-r", str(SAMPLE_RATE),
                    "-c", str(CHANNELS),
                    "-t", "raw",
                    "--period-size", str(SAMPLES_PER_FRAME),
                    "--buffer-size", str(SAMPLES_PER_FRAME * 4),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )
            threading.Thread(target=self._log_stderr, daemon=True).start()

        bytes_needed = SAMPLES_PER_FRAME * CHANNELS * 2

        try:
            data = await asyncio.to_thread(self._read_exact, bytes_needed)
        except EOFError:
            pass

        frame = AudioFrame(format="s16", layout="stereo", samples=SAMPLES_PER_FRAME)
        frame.planes[0].update(data)
        frame.sample_rate = SAMPLE_RATE
        frame.pts = self.timestamp
        frame.time_base = Fraction(1, SAMPLE_RATE)
        self.timestamp += SAMPLES_PER_FRAME
        return frame

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.kill()
