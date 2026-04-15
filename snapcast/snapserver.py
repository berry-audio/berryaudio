import asyncio
import json
import logging
import re
import subprocess
import threading

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Awaitable

import websockets

logger = logging.getLogger(__name__)

SNAPSERVER_PATH = "/usr/local/bin/snapserver"
SNAPSERVER_CONFIG_PATH = Path(__file__).parent / "snapserver.conf"

JSONRPC_PORT = 1705
AUDIO_PORT = 1704
WS_PORT = 1780
LOCAL_IP = "127.0.0.1"

WS_PING_INTERVAL = 20
WS_PING_TIMEOUT = 10
WS_RECONNECT_DELAY = 3
JSONRPC_TIMEOUT = 2.0

BIT_DEPTH = 32


@dataclass
class SnapServerConfig:
    hostname: str
    playback_device: str
    codec: str
    chunk_ms: int
    buffer_ms: int


@dataclass
class SnapClient:
    id: str
    name: str
    ip: str
    os: str
    connected: bool = True


@dataclass
class SnapStream:
    id: str
    status: str
    codec: str = ""
    sampleformat: str = ""


@dataclass
class SnapServerState:
    running: bool = False
    clients: dict[str, SnapClient] = field(default_factory=dict)
    streams: dict[str, SnapStream] = field(default_factory=dict)


class SnapServer:
    """
    Manages a local snapserver process and its JSON-RPC / WebSocket interfaces.

    Lifecycle:
        await server.start(sample_rate)   # spawn process + connect listeners
        await server.stop()               # terminate process + disconnect

    Callbacks (all async):
        on_ready          ()                       — process started, RPC reachable
        on_client_connect (client: SnapClient)     — a client connected
        on_client_disconnect (client: SnapClient)  — a client disconnected
        on_stream_update  (stream: SnapStream)     — stream status changed

    Control API:
        await server.get_status()                  -> dict
        await server.set_client_volume(id, vol, muted)
        await server.set_client_name(id, name)
        await server.set_client_latency(id, ms)
        await server.delete_client(id)

    Properties:
        server.state      — SnapServerState snapshot
        server.ip         — LOCAL_IP when running, else None
    """

    def __init__(self, config: SnapServerConfig):
        self._config = config
        self._proc: subprocess.Popen | None = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._ws_task: asyncio.Task | None = None
        self._ws_running = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._state = SnapServerState()
        self._rpc_id = 0

        self.on_ready: Callable[[], Awaitable] | None = None
        self.on_client_connect: Callable[[SnapClient], Awaitable] | None = None
        self.on_client_disconnect: Callable[[SnapClient], Awaitable] | None = None
        self.on_stream_update: Callable[[SnapStream], Awaitable] | None = None

    @property
    def state(self) -> SnapServerState:
        return self._state

    @property
    def ip(self) -> str | None:
        return LOCAL_IP if self._state.running else None

    async def start(self, sample_rate: int) -> None:
        if self._proc is not None:
            logger.debug("Snapserver already running")
            return

        self._loop = asyncio.get_running_loop()
        self._launch_process(sample_rate)

    async def stop(self) -> None:
        await self._stop_ws()
        await self._disconnect_rpc()

        if self._proc is not None:
            self._proc.terminate()
            try:
                await self._loop.run_in_executor(
                    None, self._proc.wait, 3
                )
            except Exception:
                self._proc.kill()
            self._proc = None

        self._state.running = False
        self._state.clients.clear()
        self._state.streams.clear()
        logger.info("Snapserver stopped")

    # ------------------------------------------------------------------ #
    # Control API                                                          #
    # ------------------------------------------------------------------ #

    async def get_status(self) -> dict:
        result = await self._rpc("Server.GetStatus")
        if not result:
            return {}

        self._sync_state(result)
        return result

    async def set_client_volume(
        self, client_id: str, volume: int, muted: bool = False
    ) -> dict | None:
        return await self._rpc(
            "Client.SetVolume",
            {"id": client_id, "volume": {"percent": volume, "muted": muted}},
        )

    async def set_client_name(self, client_id: str, name: str) -> dict | None:
        return await self._rpc("Client.SetName", {"id": client_id, "name": name})

    async def set_client_latency(self, client_id: str, latency_ms: int) -> dict | None:
        return await self._rpc(
            "Client.SetLatency", {"id": client_id, "latency": latency_ms}
        )

    async def delete_client(self, client_id: str) -> dict | None:
        result = await self._rpc("Server.DeleteClient", {"id": client_id})
        if result:
            self._state.clients.pop(client_id, None)
        return result

    async def set_stream(self, group_id: str, stream_id: str) -> dict | None:
        return await self._rpc(
            "Group.SetStream", {"id": group_id, "stream_id": stream_id}
        )

    # ------------------------------------------------------------------ #
    # Process                                                              #
    # ------------------------------------------------------------------ #

    def _launch_process(self, sample_rate: int) -> None:
        cmd = [
            SNAPSERVER_PATH,
            "-c", str(SNAPSERVER_CONFIG_PATH),
            "--stream.codec", self._config.codec,
            "--stream.chunk_ms", str(self._config.chunk_ms),
            "--stream.buffer", str(self._config.buffer_ms),
            "--stream.source",
            (
                f"alsa://?name=Loopback"
                f"&device={self._config.playback_device}"
                f"&devicename={self._config.hostname}"
                f"&sampleformat={sample_rate}:{BIT_DEPTH}:2"
            ),
        ]

        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        for stream, label in [
            (self._proc.stdout, "stdout"),
            (self._proc.stderr, "stderr"),
        ]:
            threading.Thread(
                target=self._log,
                args=(stream, label),
                daemon=True,
            ).start()

        logger.info(f"Snapserver process started (pid={self._proc.pid})")

    def _log(self, stream, label: str) -> None:
        for line in iter(stream.readline, ""):
            stripped = line.strip()
            if not stripped:
                continue
            logger.debug(f"[snapserver/{label}] {stripped}")

            if "successfully established" in stripped:
                self._loop.call_soon_threadsafe(
                    asyncio.ensure_future,
                    self._on_process_ready(),
                )

        stream.close()

    async def _on_process_ready(self) -> None:
        self._state.running = True
        await self._connect_rpc()
        await self.get_status()
        await self._start_ws()

        logger.info(f"Snapserver ready at {LOCAL_IP}:{AUDIO_PORT}")

        if self.on_ready:
            await self.on_ready()

    # ------------------------------------------------------------------ #
    # JSON-RPC (TCP)                                                       #
    # ------------------------------------------------------------------ #

    async def _connect_rpc(self) -> None:
        await self._disconnect_rpc()
        try:
            self._reader, self._writer = await asyncio.open_connection(
                LOCAL_IP, JSONRPC_PORT
            )
        except OSError as e:
            logger.error(f"RPC connect failed: {e}")

    async def _disconnect_rpc(self) -> None:
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None

    async def _rpc(self, method: str, params: dict | None = None) -> dict | None:
        if not self._writer or self._writer.is_closing():
            await self._connect_rpc()
            if not self._writer:
                return None

        self._rpc_id += 1
        request = {"id": self._rpc_id, "jsonrpc": "2.0", "method": method}
        if params:
            request["params"] = params

        try:
            self._writer.write((json.dumps(request) + "\n").encode())
            await self._writer.drain()

            raw = await asyncio.wait_for(
                self._reader.readline(), timeout=JSONRPC_TIMEOUT
            )
            if not raw:
                return None

            response = json.loads(raw.decode())

            if "error" in response:
                logger.warning(f"RPC error [{method}]: {response['error']}")
                return None

            return response.get("result")

        except (asyncio.TimeoutError, OSError, json.JSONDecodeError) as e:
            logger.warning(f"RPC request failed [{method}]: {e}")
            await self._disconnect_rpc()
            return None

    # ------------------------------------------------------------------ #
    # WebSocket notification listener                                      #
    # ------------------------------------------------------------------ #

    async def _start_ws(self) -> None:
        await self._stop_ws()
        self._ws_running = True
        self._ws_task = asyncio.create_task(self._ws_loop())

    async def _stop_ws(self) -> None:
        self._ws_running = False
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
            self._ws_task = None
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def _ws_loop(self) -> None:
        while self._ws_running:
            try:
                await self._ws_connect_and_listen()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._ws_running:
                    logger.warning(
                        f"WS disconnected: {e}. Reconnecting in {WS_RECONNECT_DELAY}s"
                    )
                    await asyncio.sleep(WS_RECONNECT_DELAY)

    async def _ws_connect_and_listen(self) -> None:
        uri = f"ws://{LOCAL_IP}:{WS_PORT}/jsonrpc"
        async with websockets.connect(
            uri,
            ping_interval=WS_PING_INTERVAL,
            ping_timeout=WS_PING_TIMEOUT,
        ) as ws:
            self._ws = ws
            logger.debug("Snapserver WS connected")

            async for raw in ws:
                await self._dispatch_notification(raw)

        self._ws = None

    async def _dispatch_notification(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return

        method = msg.get("method")
        params = msg.get("params", {})

        if not method:
            return

        handlers = {
            "Client.OnConnect": self._on_client_connect,
            "Client.OnDisconnect": self._on_client_disconnect,
            "Stream.OnUpdate": self._on_stream_update,
            "Server.OnUpdate": self._on_server_update,
        }

        handler = handlers.get(method)
        if handler:
            try:
                await handler(params)
            except Exception as e:
                logger.error(f"Notification handler error [{method}]: {e}")
        else:
            logger.debug(f"Unhandled notification: {method}")

    # ------------------------------------------------------------------ #
    # Notification handlers                                                #
    # ------------------------------------------------------------------ #

    async def _on_client_connect(self, params: dict) -> None:
        raw = params.get("client", {})
        host = raw.get("host", {})
        client = SnapClient(
            id=raw.get("id", host.get("ip", "")),
            name=host.get("name", "unknown"),
            ip=host.get("ip", ""),
            os=host.get("os", "unknown"),
            connected=True,
        )
        self._state.clients[client.id] = client
        logger.info(f"Client connected: {client.name} ({client.ip})")

        if self.on_client_connect:
            await self.on_client_connect(client)

    async def _on_client_disconnect(self, params: dict) -> None:
        raw = params.get("client", {})
        host = raw.get("host", {})
        client_id = raw.get("id", host.get("ip", ""))

        client = self._state.clients.get(client_id)
        if client:
            client.connected = False
            logger.warning(f"Client disconnected: {client.name} ({client.ip})")
        else:
            client = SnapClient(
                id=client_id,
                name=host.get("name", "unknown"),
                ip=host.get("ip", ""),
                os=host.get("os", "unknown"),
                connected=False,
            )

        if self.on_client_disconnect:
            await self.on_client_disconnect(client)

    async def _on_stream_update(self, params: dict) -> None:
        raw = params.get("stream", {})
        stream = SnapStream(
            id=raw.get("id", ""),
            status=raw.get("status", "unknown"),
        )
        self._state.streams[stream.id] = stream
        logger.info(f"Stream updated: {stream.id} → {stream.status}")

        if self.on_stream_update:
            await self.on_stream_update(stream)

    async def _on_server_update(self, params: dict) -> None:
        logger.debug("Server.OnUpdate — resyncing state")
        await self.get_status()

    # ------------------------------------------------------------------ #
    # State sync                                                           #
    # ------------------------------------------------------------------ #

    def _sync_state(self, result: dict) -> None:
        server_block = result.get("server", {})

        for stream_data in server_block.get("streams", []):
            sid = stream_data.get("id", "")
            self._state.streams[sid] = SnapStream(
                id=sid,
                status=stream_data.get("status", "unknown"),
            )

        for group in server_block.get("groups", []):
            for client_data in group.get("clients", []):
                host = client_data.get("host", {})
                cid = client_data.get("id", host.get("ip", ""))
                self._state.clients[cid] = SnapClient(
                    id=cid,
                    name=host.get("name", "unknown"),
                    ip=host.get("ip", ""),
                    os=host.get("os", "unknown"),
                    connected=client_data.get("connected", False),
                )