import logging
import threading
import subprocess
import asyncio
import os
import re
import socket
import json
import aiohttp
import websockets

from pathlib import Path
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser
from core.util.system import SystemUtil
from core.models import Track, Source, Room, Album, Artist
from core.actor import SourceActor

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_snapcast._tcp.local."
SNAPCAST_LOCAL_IP = "127.0.0.1"
DISCOVERY_TIME = 2

SERVER_WS_PORT = 1780
JSONRPC_PORT = 1705
AUDIO_PORT = 1704

SNAPSERVER_PATH = "/usr/local/bin/snapserver"
SNAPCLIENT_PATH = "/usr/local/bin/snapclient"
SNAPSERVER_CONFIG_PATH = Path(__file__).parent / "snapserver.conf"

SAMPLE_FORMAT_MAP = {
    "S16_LE": 16,
    "S24_LE": 24,
    "S32_LE": 32,
}


class MultiroomExtension(SourceActor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._hostname = self._config["system"].get("hostname")
        self._server_enabled = self._config["multiroom"].get("server")
        self._server_codec = self._config["multiroom"].get("codec")
        self._server_chunk = self._config["multiroom"].get("chunk")
        self._server_buffer = self._config["multiroom"].get("buffer")
        self._client_device = self._config["multiroom"].get("client_device")
        self._server_device = self._config["multiroom"].get("server_device")
        self._system = SystemUtil(self._core, self._db)
        self._mac = self._system.get_mac()
        self._proc_snapclient = None
        self._proc_snapserver = None
        self._server_ws = None
        self._server_notification_task = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._servers = {}
        self.jsonrpc_timeout = 5
        self.zeroconf = AsyncZeroconf()
        self._source = Source(
            name="Multiroom",
            uri=self._name,
            enabled=False,
            controls=[],
            state={
                "icon": "speaker",
            },
        )
        self._sample_rate = 44100
        self._bit_depth = self._config["multiroom"].get("bit_depth", 32)
        self._track = Track()
        self._zc_tasks = set()
        self._loop = asyncio.get_running_loop()
        self._server_notification_tasks = {}
        self._server_websockets = {}

    async def on_config_update(self, config):
        updated_config = config[self._name]
        if not updated_config:
            return

        if "server" in updated_config:
            self._server_enabled = updated_config["server"]

        if "codec" in updated_config:
            self._server_codec = updated_config["codec"]

        if "chunk" in updated_config:
            self._server_chunk = updated_config["chunk"]

        if "buffer" in updated_config:
            self._server_buffer = updated_config["buffer"]

        await self._control_snapserver()

    def _enabled_state(self):
        self._source.enabled = os.path.exists(SNAPSERVER_PATH) and os.path.exists(SNAPCLIENT_PATH)

    async def on_event(self, message):
        event = message.get("event")
        if event == "dsp_options_changed":
            self._sample_rate = message.get("sample_rate", self._sample_rate)
            self._bit_depth = SAMPLE_FORMAT_MAP.get(message.get("sample_format", self._bit_depth))
            # await self._control_snapserver()

        if event == "track_meta_updated":
            await self.on_servers()
            if SNAPCAST_LOCAL_IP in self._servers:
                self._core.send(
                    target=["web", "display"],
                    event="multiroom_server_updated",
                    server=self._servers[SNAPCAST_LOCAL_IP],
                )

    async def on_start_service(self):
        return self._source

    async def on_stop_service(self):
        await self._core.request("playback.clear")

        if self._source.state.address:
            await self._stop_notification_listener(self._source.state.address)
            self._source.state.name = None
            self._source.state.icon = None
            self._source.state.connected = False
            self._source.state.address = None
            await self.on_stop_snapclient()
            await self._send_connection_update(self._source.state.address)
        return True

    """Zeroconf default callbacks"""
    def _manage_service(self, **kwargs):
        task = asyncio.create_task(self._service_handler(kwargs))
        self._zc_tasks.add(task)
        task.add_done_callback(self._zc_tasks.discard)

    async def _service_handler(self, kwargs):
        service_state = str(kwargs.get("state_change"))
        service_name = kwargs.get("name")

        if service_state == "ServiceStateChange.Added":
            service_type = kwargs.get("service_type")
            service_name = kwargs.get("name")

            if not service_type or not service_name:
                return

            info = await self.zeroconf.async_get_service_info(
                service_type, service_name
            )

            if not info:
                return

            ips = []
            for addr in info.addresses:
                try:
                    ips.append(socket.inet_ntoa(addr))
                except Exception:
                    continue

            if not ips:
                return

            hostname = (
                info.server.rstrip(".") if info.server else "Unknown"
            ).removesuffix(".local")

            resolved_ip = ips[0]
            if hostname.lower() == socket.gethostname().lower():
                resolved_ip = SNAPCAST_LOCAL_IP

            self._servers[resolved_ip] = Room(
                service_name=service_name,
                name=hostname,
                ip=resolved_ip,
                port=info.port,
                connected=False,
                status=None,
            )

            self._servers[resolved_ip].status = await self.on_get_status(self._servers[resolved_ip].ip)
            self._core.send(
                target=["web", "display"],
                event="multiroom_server_updated",
                server=self._servers[resolved_ip],
            )
            logger.info(
                f"Multiroom updated server {self._servers[resolved_ip].name} ({self._servers[resolved_ip].ip})")

        if service_state == "ServiceStateChange.Removed":
            for server in await self.on_servers():
                if server.service_name == service_name:
                    await self._stop_notification_listener(server.ip)
                    self._core.send(
                        target=["web", "display"],
                        event="multiroom_server_updated",
                        server=self._servers[server.ip],
                    )

    async def _send_request_rpc(self, ip, request, port=8080, timeout=1.0):
        url = f"http://{ip}:{port}/rpc"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request, timeout=timeout) as resp:
                return await resp.json()

    async def _send_request(self, ip, request):
        self._reader, self._writer = await asyncio.open_connection(ip, JSONRPC_PORT)
        self._writer.write((json.dumps(request) + "\n").encode())
        await self._writer.drain()
        try:
            response = await asyncio.wait_for(self._reader.readline(), timeout=1.0)
            logger.debug(request)
            if response:
                result = json.loads(response.decode())
                if "error" in result:
                    logger.error(result["error"])

                if self._writer:
                    try:
                        self._writer.close()
                        await self._writer.wait_closed()
                    except Exception as e:
                        logger.debug(f"Error closing connection: {e}")
                    finally:
                        self._writer = None
                        self._reader = None
                        self._connected_ip = None
                return result.get("result")
        except asyncio.TimeoutError:
            return None

    async def _send_connection_update(self, ip):
        await self.on_servers()
        server = self._servers[ip]
        if self._source.state.connected:
            self._core.send(
                target=["web", "display"], event="multiroom_server_connected", server=server)
            logger.info(f"Multiroom connected to {ip}:{AUDIO_PORT}")
        else:
            self._core.send(
                target=["web", "display"], event="multiroom_server_disconnected", server=server)
            logger.warning("Multiroom disconnected")

    async def on_start(self):
        if not os.path.exists(SNAPSERVER_PATH):
            logger.error("Multiroom server missing")

        if not os.path.exists(SNAPCLIENT_PATH):
            logger.error("Multiroom client missing")

        if not os.path.exists(SNAPSERVER_CONFIG_PATH):
            logger.error("Multiroom config missing")

        self._enabled_state()

        AsyncServiceBrowser(
            self.zeroconf.zeroconf,
            SERVICE_TYPE,
            handlers=[
                self._manage_service,
            ],
        )

        logger.info("Started")

    async def on_stop(self):
        await self.zeroconf.async_close()
        for ip, ws in list(self._server_websockets.items()):
            try:
                await ws.close()
                logger.info(f"Closed notification websocket: {ip}")
            except Exception as e:
                logger.warning(f"Error closing websocket for {ip}: {e}")
            finally:
                self._server_websockets.pop(ip, None)

        await self.on_stop_snapclient()
        await self.on_stop_snapserver()
        logger.info("Stopped")

    async def _control_snapserver(self):
        if self._server_enabled:
            await self.on_start_snapserver()
        else:
            await self.on_stop_snapserver()

    async def on_stop_snapserver(self):
        if self._proc_snapserver is not None:
            self._proc_snapserver.terminate()
            self._proc_snapserver.kill()
            self._proc_snapserver = None

            for server in list(self._servers.values()):
                if server.ip == SNAPCAST_LOCAL_IP:
                    await self._stop_notification_listener(SNAPCAST_LOCAL_IP)
                    del self._servers[SNAPCAST_LOCAL_IP]

            logger.info(f"Multiroom server stopped")

    async def on_start_snapserver(self, sample_rate=44100, bit_depth='S32_LE'):
        if not self._server_enabled:
             return
         
        if self._proc_snapserver is not None:
            return

        if not os.path.exists(SNAPSERVER_PATH):
            return

        self._sample_rate = sample_rate if sample_rate else self._sample_rate
        self._bit_depth = SAMPLE_FORMAT_MAP.get(bit_depth) if bit_depth else self._bit_depth

        cmd = [
            SNAPSERVER_PATH,
            "-c",
            SNAPSERVER_CONFIG_PATH,
            "--stream.codec",
            self._server_codec,
            "--stream.chunk_ms",
            str(self._server_chunk),
            "--stream.buffer",
            str(self._server_buffer),
            "--stream.source",
            f"alsa://?name=Loopback"
            f"&device={self._server_device}"
            f"&devicename={self._hostname}"
            f"&sampleformat={self._sample_rate}:{self._bit_depth}:2",
        ]

        self._proc_snapserver = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        async def _on_connected():
            logger.info(
                f"Snapcast server started with {self._sample_rate}:{self._bit_depth}:2")
            await self._start_notification_listener(SNAPCAST_LOCAL_IP)

        def _log(stream, label):
            for line in iter(stream.readline, ""):
                logger.debug(line.strip())

                if "successfully established" in line:
                    self._loop.call_soon_threadsafe(
                        asyncio.create_task, _on_connected()
                    )

                if "Invalid argument" in line:
                    self._core.send(
                        target=["web", "display"],
                        event="error",
                        message=line,
                    )

            stream.close()

        threading.Thread(
            target=_log, args=(self._proc_snapserver.stdout, "STDOUT"), daemon=True
        ).start()

        threading.Thread(
            target=_log, args=(self._proc_snapserver.stderr, "STDERR"), daemon=True
        ).start()
        
        logger.info(
            f"Multiroom server started at {SNAPCAST_LOCAL_IP}:{AUDIO_PORT}")

    async def on_stop_snapclient(self):
        """Multiroom client stop"""
        if self._proc_snapclient is None:
            return

        self._proc_snapclient.terminate()
        self._proc_snapclient.kill()
        self._proc_snapclient = None
        await self._core.request("playback.clear")
        logger.info(f"Multiroom client stopped")

    async def on_start_snapclient(self, ip):
        """Multiroom client initialization"""
        if self._proc_snapclient is not None:
            return

        if not os.path.exists(SNAPCLIENT_PATH):
            return
        
        cmd = [
            SNAPCLIENT_PATH,
            f"tcp://{ip}:{AUDIO_PORT}",
            "--player",
            "alsa",
            "--soundcard",
            f"{self._client_device}",
        ]
        self._proc_snapclient = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
        )

        async def _client_disconnected():
            await self.on_servers()
            await self.on_disconnect()
            logger.error('Failed to connect.Room offline or unreachable')
            self._core.send(
                target=["web", "display"],
                event="error",
                message="Room offline or unreachable",
            )

        async def _client_connected():
            server = self._servers[ip]
            self._source.state.icon = "speaker"
            self._source.state.connected = True
            self._source.state.address = ip
            self._source.state.name = server.name
            await self._send_connection_update(ip)
            await self._start_notification_listener(ip)
            await self._core.request("source.set", uri="multiroom")
            await self._core.request("source.update_source", source=self._source)

        async def _client_errors(line):
            await self._core.request("playback.clear")
            logger.error(line)
            self._core.send(
                target=["web", "display"],
                event="error",
                message=line,
            )

        def _log(stream, label):
            for line in iter(stream.readline, ""):
                logger.debug(line.strip())

                # Parse Codec info
                CODEC_RE = re.compile(
                    r"Codec:\s*(?P<codec>\w+),\s*sampleformat:\s*(?P<sampleformat>[\d:]+)"
                )
                match = CODEC_RE.search(line)
                if match:
                    codec = match.group("codec")
                    sampleformat = match.group("sampleformat")

                    if sampleformat:
                        rate, bit_depth, channels = map(
                            int, sampleformat.split(":"))

                    self._track = Track(
                        uri=self._name,
                        name=self._source.state.name,
                        albums=frozenset([Album(name="Multiroom")]),
                        artists=frozenset([Artist(name="Multiroom")]),
                        sample_rate=rate,
                        bit_depth=f"{bit_depth}bit",
                        channels=channels,
                        audio_codec=codec,
                    )

                    self._core._request(
                        "playback.set_metadata", track=self._track)

                if "Connected" in line:
                    self._loop.call_soon_threadsafe(
                        asyncio.create_task, _client_connected()
                    )

                if "Failed to connect to host" in line:
                    self._loop.call_soon_threadsafe(
                        asyncio.create_task, _client_disconnected()
                    )

                if "Exception in" in line:
                    self._loop.call_soon_threadsafe(
                        asyncio.create_task, _client_errors(line)
                    )

            stream.close()

        threading.Thread(
            target=_log, args=(self._proc_snapclient.stdout, "STDOUT"), daemon=True
        ).start()

        threading.Thread(
            target=_log, args=(self._proc_snapclient.stderr, "STDERR"), daemon=True
        ).start()

    async def on_servers(self):
        servers = []
        await asyncio.sleep(0.1)
        for server in list(self._servers.values()):
            server.connected = server.ip == self._source.state.address
            server.status = await self.on_get_status(server.ip)
            self._servers[server.ip] = server
            servers.append(server)

        return servers

    async def on_disconnect(self, ip=None):
        ip = ip if ip else self._source.state.address
        await self._stop_notification_listener(ip)

        self._source.state.name = None
        self._source.state.icon = None
        self._source.state.connected = False
        self._source.state.address = None
        await self._core.request("source.update_source", source=self._source)
        await self._core.request("playback.clear")

        await self.on_stop_snapclient()
        await self._send_connection_update(ip)
        return True

    async def on_connect(self, ip):
        await self.on_start_snapclient(ip)
        return True

    async def on_add_stream(self, ip):
        request = {
            "id": 8,
            "jsonrpc": "2.0",
            "method": "Stream.AddStream",
            "params": {
                "streamUri": f"alsa:///?name=Loopback1&sampleformat={self._sample_rate}:{self._bit_depth}:2&device=hw:Loopback,1,2"
            }
        }
        result = await self._send_request(ip, request)
        return result

    async def on_remove_stream(self, ip):
        request = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "Stream.RemoveStream",
            "params": {
                "id": "Loopback"
            }
        }
        result = await self._send_request(ip, request)
        return result

    async def on_get_status(self, ip):
        request = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "Server.GetStatus",
        }
        request_meta = {
            "id": 2,
            "jsonrpc": "2.0",
            "method": "playback.get_current_tl_track",
        }
        response_status = {}
        try:
            response_status = await self._send_request(ip, request)
            response_meta = await self._send_request_rpc(ip, request_meta)
            if response_status['server']['streams']:
                response_status['server']['streams'][0]['meta'] = response_meta.get(
                    'result', None)
        except (OSError, Exception) as e:
            logger.warning(f"Failed to get status for {ip}: {e}")
            response_status = {}
        return response_status

    async def on_set_volume(self, ip, client_id, volume=None, mute=False):
        request = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "Client.SetVolume",
            "params": {"id": client_id, "volume": {"muted": mute, "percent": volume}},
        }
        result = await self._send_request(ip, request)
        return result

    async def _start_notification_listener(self, ip):
        if ip in self._server_notification_tasks:
            task = self._server_notification_tasks[ip]

            if not task.done():
                return

        task = asyncio.create_task(
            self._handle_notifications(ip)
        )
        self._server_notification_tasks[ip] = task

    async def _stop_notification_listener(self, ip):
        task = self._server_notification_tasks.pop(ip, None)
        if task:
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass
        ws = self._server_websockets.pop(ip, None)
        if ws:
            await ws.close()

    async def _handle_notifications(self, ip):
        """Handle WebSocket notifications"""
        try:
            ws = await websockets.connect(
                f"ws://{ip}:{SERVER_WS_PORT}/jsonrpc",
                ping_interval=20,
                ping_timeout=10,
            )

            self._server_websockets[ip] = ws
            logger.info(f"Notification websocket connected: {ip}")

            async for message in ws:
                msg = json.loads(message)

                logger.debug(msg)
                method = msg.get("method")
                params = msg.get("params")

                if not method or not params:
                    return

                if ip not in self._servers:
                    return

                if method == "Client.OnConnect":
                    client = params.get("client", {})
                    self._servers[ip].status = await self.on_get_status(ip)
                    self._core.send(
                        target=["web", "display"],
                        event="multiroom_client_connected",
                        client=client,
                    )

                    logger.info(f"Client connected: {client}")

                    if ip == SNAPCAST_LOCAL_IP:
                        for server in self._servers.values():
                            if not server.connected:
                                continue
                            for group in server.status.get("server", {}).get("groups", []):
                                for client in group.get("clients", []):
                                    client_mac = client.get(
                                        "host", {}).get("mac", "").lower()
                                    if client_mac == self._mac:
                                        logger.warning(
                                            f"Circular connection detected on {server.name} ({server.ip}); disconnecting")
                                        await self.on_disconnect()
                                        break

                    if ip in self._servers:
                        self._core.send(
                            target=["web", "display"],
                            event="multiroom_server_updated",
                            server=self._servers[ip],
                        )

                elif method == "Client.OnDisconnect":
                    client = params.get("client", {})
                    self._servers[ip].status = await self.on_get_status(ip)
                    self._core.send(
                        target=["web", "display"],
                        event="multiroom_client_disconnected",
                        client=client,
                    )
                    self._core.send(
                        target=["web", "display"],
                        event="multiroom_server_updated",
                        server=self._servers[ip],
                    )
                    logger.warning(f"Client disconnected: {client}")

                elif method == "Stream.OnUpdate":
                    stream = params.get("stream", {})
                    self._servers[ip].status = await self.on_get_status(ip)
                    logger.info(
                        f"Stream updated: {stream.get('id')} status={stream.get('status')}"
                    )
                    self._core.send(
                        target=["web", "display"],
                        event="multiroom_stream_update",
                        stream=stream,
                    )
                    self._core.send(
                        target=["web", "display"],
                        event="multiroom_server_updated",
                        server=self._servers[ip],
                    )

        except asyncio.CancelledError:
            logger.debug(f"Notification listener cancelled {ip}")
            raise

        except (
            websockets.exceptions.ConnectionClosed,
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
        ) as e:
            logger.warning(f"WebSocket closed, reconnecting in 3s: {e}")
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Notification listener error: {e}")
            await asyncio.sleep(1)

        finally:
            if self._server_websockets.get(ip) is ws:
                self._server_websockets.pop(ip, None)
            logger.info(f"Notification websocket disconnected: {ip}")
