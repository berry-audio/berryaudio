import logging
import threading
import subprocess
import asyncio
import socket
import os
import re
import socket
import json
import websockets

from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser
from zeroconf._exceptions import NotRunningException
from core.models import Album, Track, TlTrack, Source
from pathlib import Path
from core.actor import Actor

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_snapcast._tcp.local."
SNAPCAST_LOCAL_IP  = "127.0.0.1"
DISCOVERY_TIME = 5

SERVER_WS_PORT = 1780
JSONRPC_PORT = 1705
AUDIO_PORT = 1704

SNAPSERVER_PATH = "/usr/local/bin/snapserver"
SNAPCLIENT_PATH = "/usr/local/bin/snapclient"
SNAPSERVER_CONFIG_PATH = Path(__file__).parent / "snapserver.conf"

DEFAULT_CONFIG = {
    "snapserver": 0,
    "source_name": "Loopback",
    "source": "hw:Loopback,1,1",
    "codec": "pcm",
    "buffer": 200,
}


class SnapcastExtension(Actor):
    def __init__(self, core, db, config):
        super().__init__()
        self._loop = asyncio.get_running_loop()
        self._core = core
        self._db = db
        self._config = config
        self._proc_snapclient = None
        self._proc_snapserver = None
        self._server = None
        self._server_ws = None
        self._server_notification_task = None
        self._device = self._config["playback"]["output_device"]
        self.servers = {}
        self.jsonrpc_timeout = 5
        self.zeroconf = AsyncZeroconf()
        self._source = Source(
            type='snapcast', 
            controls=[], 
            state={
                'icon': 'speaker',
            }) 
        self._tl_track = TlTrack(0, track=Track(
                        name =  "Snapcast",
                        albums = frozenset([Album(name = "Unknown")]),
                    ))


    async def on_start_service(self):
        await self._meta_init()
        return True
    

    async def on_stop_service(self):
        await self._core.request("playback.clear")
        await self._stop_snapclient()
        await self._init_snapserver()
        return True


    async def _meta_init(self):
        """Reset metadata handling"""
        await self._core.request("playback.set_metadata", tl_track=self._tl_track)


    """Zeroconf default callbacks"""

    def add_service(self, **kwargs):
        asyncio.create_task(self._handle_service(kwargs))

    def update_service(self, **kwargs):
        asyncio.create_task(self._handle_service(kwargs))

    def remove_service(self, **kwargs):
        name = kwargs.get("name")
        if name:
            self.servers.pop(name, None)


    """Snapcast functions"""

    async def _send_request(self, ip, request, port=JSONRPC_PORT):
        if not ip:
            raise RuntimeError("Invalid or no IP address defined")

        reader, writer = await asyncio.open_connection(ip, port)
        writer.write((json.dumps(request) + "\n").encode())
        await writer.drain()

        response = await reader.readline()
        writer.close()
        await writer.wait_closed()

        result = json.loads(response.decode())

        if "error" in result:
            raise RuntimeError(result["error"])

        return result.get("result")


    async def _get_reverse_dns(self, ip):
        try:
            hostname, _, _ = await self._loop.run_in_executor(None, socket.gethostbyaddr, ip)
            return hostname
        except Exception:
            return None


    async def _get_hostname(self, ip):
        request = {"jsonrpc": "2.0", "id": 1, "method": "Server.GetStatus"}
        _result = await self._send_request(ip, request, JSONRPC_PORT)
        return _result["server"]["hostname"]


    async def _update_source(self, ip):
        self._source.state.name = await self._get_reverse_dns(ip)

        _track =  self._tl_track.track.copy(update={
                            "albums": frozenset([Album(name = self._source.state.name or self._source.state.address or "Unknown")]),
                        })
                           
        self._tl_track = TlTrack(tlid=self._tl_track.tlid, track=_track)
        self._core.send(event='track_meta_updated',  tl_track=self._tl_track)
        await self._core.request("source.update_source", source=self._source)    


    async def _handle_service(self, kwargs):
        try:
            service_type = kwargs.get("service_type")
            name = kwargs.get("name")

            if not service_type or not name:
                return

            info = await self.zeroconf.async_get_service_info(service_type, name)
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
                info.server.rstrip(".")
                if info.server
                else await self._get_hostname(ips[0])
                or await self._get_reverse_dns(ips[0])
                or "Unknown"
            ).removesuffix(".local")

            self.servers[name] = {
                "service_name": name,
                "hostname": hostname,
                "ip": ips,
                "port": info.port,
            }

        except NotRunningException:
            return
        except Exception:
            return


    async def on_start(self):
        if not os.path.exists(SNAPSERVER_PATH):
            logger.error("Snapcast server missing")
            return

        if not os.path.exists(SNAPCLIENT_PATH):
            logger.error("Snapcast client missing")
            return

        if not os.path.exists(SNAPSERVER_CONFIG_PATH):
            logger.error("Snapcast config missing")
            return

        self._db.init_extension("snapcast", DEFAULT_CONFIG)

        await self._init_snapserver()
        logger.info("Started")


    async def on_event(self, message):
        pass


    async def on_stop(self):
        await self.zeroconf.async_close()

        await self._stop_snapserver()
        await self._stop_snapclient()

        self._server = None
        logger.info("Stopped")


    async def _stop_snapserver(self):
        """Snapcast server stop"""
        if self._proc_snapserver is not None:
            await self._stop_notification_listener()
            self._proc_snapserver.terminate()
            self._proc_snapserver.kill()
            self._proc_snapserver = None

            logger.info(f"Snapcast server stopped")


    async def _init_snapserver(self):
        """Snapcast server initialization"""

        if self._config["snapcast"]["snapserver"] == 1:
            if self._proc_snapserver is not None:
                return False # already running

            cmd = [
                SNAPSERVER_PATH,
                "-c",
                SNAPSERVER_CONFIG_PATH,
            ]
            self._proc_snapserver = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
            )

            self._server = SNAPCAST_LOCAL_IP

            def _log(stream, label):
                for line in iter(stream.readline, ""):
                    logger.debug(line.strip())

                    if "successfully established" in line:
                        self._loop.call_soon_threadsafe(
                            asyncio.create_task, self._start_notification_listener()
                        )

                stream.close()

            threading.Thread(
                target=_log, args=(self._proc_snapserver.stdout, "STDOUT"), daemon=True
            ).start()

            threading.Thread(
                target=_log, args=(self._proc_snapserver.stderr, "STDERR"), daemon=True
            ).start()
            
            logger.info(f"Snapcast server started at {self._server}:{AUDIO_PORT}")


    async def _stop_snapclient(self):
        """Snapcast client stop"""
        if self._proc_snapclient is not None:
            await self._stop_notification_listener()
            self._proc_snapclient.terminate()
            self._proc_snapclient.kill()
            self._proc_snapclient = None
            self._server = None
            self._source.state.connected = False
            await self._core.request("source.update_source", source=self._source)    
            
            logger.info(f"Snapcast client stopped")


    async def _init_snapclient(self, ip):
        """Snapcast client initialization"""

        cmd = [
            SNAPCLIENT_PATH,
            f"tcp://{ip}:{AUDIO_PORT}",
            "--player",
            "alsa",
            "--soundcard",
            self._device,
        ]
        self._proc_snapclient = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
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
                        rate, bit_depth, channels = map(int, sampleformat.split(":"))

                    _track =  self._tl_track.track.copy(update={
                            "audio_codec": codec,
                            "sample_rate": rate,
                            "channels": channels,
                            "bit_depth": f"{bit_depth}bit",
                        })
                           
                    self._tl_track = TlTrack(tlid=self._tl_track.tlid, track=_track)
                    self._core.send(event='track_meta_updated',  tl_track=self._tl_track)

                # Connected successfully
                if "Connected" in line:
                    self._server = ip
                    self._source.state.connected = True
                    self._source.state.address = ip

                    self._loop.call_soon_threadsafe(
                        asyncio.create_task, self._update_source(ip)
                    )

                    self._loop.call_soon_threadsafe(
                        asyncio.create_task, self._start_notification_listener()
                    )

                    self._core.send(
                        event="snapcast_client_connected", server=self._server
                    )

                    logger.info(f"Client connected to {ip}:{AUDIO_PORT}")

                # Connection failed
                if "Failed to connect to host" in line:
                    self._server = None
                    self._source.state.connected = False
                    self._source.state.name = None
                    self._source.state.address = None
                    self._core.send(
                        event="snapcast_client_disconnected", server=ip
                    )
                    self._server = SNAPCAST_LOCAL_IP
                    self._loop.call_soon_threadsafe(
                        asyncio.create_task, self._stop_notification_listener()
                    )

                    logger.error(f"Client failed to connect {ip}:{AUDIO_PORT}")
            stream.close()

        threading.Thread(
            target=_log, args=(self._proc_snapclient.stdout, "STDOUT"), daemon=True
        ).start()

        threading.Thread(
            target=_log, args=(self._proc_snapclient.stderr, "STDERR"), daemon=True
        ).start()


    """api callbacks methods"""

    async def on_servers(self, rescan: bool = False):
        if self.servers and not rescan:
            return list(self.servers.values())

        AsyncServiceBrowser(
            self.zeroconf.zeroconf,
            SERVICE_TYPE,
            handlers=[
                self.add_service,
                self.update_service,
                self.remove_service,
            ],
        )

        logger.info("Discovering Snapcast servers via Avahi (mDNS)...")
        await asyncio.sleep(DISCOVERY_TIME)

        logger.debug(list(self.servers.values()))
        return list(self.servers.values())


    async def on_disconnect(self):
        await self._stop_snapclient()
        await self._init_snapserver()
        return True


    async def on_connect(self, ip):
        if not ip:
            raise RuntimeError(f"Invalid or no IP address defined")
        
        await self._core.request("playback.clear")
        await self._core.request("source.set", type='snapcast')
        await self._stop_snapserver()
        await self._stop_snapclient()
        await self._init_snapclient(ip)

        return True


    async def on_get_status(self):
        if not self._server:
            return {"clients": [], "server": {}, "streams": []}

        result_build = {}

        request = {"id": 1, "jsonrpc": "2.0", "method": "Server.GetStatus"}

        _result = await self._send_request(
            self._server, request, JSONRPC_PORT
        )
        _server = _result.get("server", {})
        _groups = _server.get("groups", [])

        result_build["clients"] = []
        for group in _groups:
            clients = group.get("clients", [])
            for client in clients:
                result_build["clients"].append(client)

        result_build["server"] = _server.get("server")
        result_build["server"]["host"]["ip"] = self._server
        result_build["streams"] = _server.get("streams")

        return result_build


    async def on_set_volume(self, client_id, volume, mute=False):
        if not self._server:
            raise RuntimeError(f"Not connected to Snapcast server")

        if not client_id:
            raise RuntimeError("client id not specified")

        request = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "Client.SetVolume",
            "params": {"id": client_id, "volume": {"muted": mute, "percent": volume}},
        }

        return await self._send_request(self._server, request, JSONRPC_PORT)


    """Snapcast notification listener functions"""

    async def _stop_notification_listener(self):
        """Stop notification listener"""
        if self._server_notification_task:
            self._server_notification_task.cancel()
            try:
                await self._server_notification_task
            except asyncio.CancelledError:
                pass
            self._server_notification_task = None

        if self._server_ws:
            await self._server_ws.close()
            self._server_ws = None


    async def _start_notification_listener(self):
        """Start notification listener"""
        await self._stop_notification_listener()

        self._server_notification_task = asyncio.create_task(
            self._handle_notifications()
        )


    async def _handle_notifications(self):
        """Handle WebSocket notifications"""
        try:
            self._server_ws = await websockets.connect(
                f"ws://{self._server}:{SERVER_WS_PORT}/jsonrpc",
                ping_interval=20,
                ping_timeout=10,
            )
            
            logger.info("Notification listener connected")
            
            async for message in self._server_ws:
                msg = json.loads(message)
                method = msg.get("method")
                params = msg.get("params")

                if not method or not params:
                    return

                client = params.get("client", {})
                host = client.get("host", {})

                name = host.get("name", "unknown")
                ip = host.get("ip", "unknown")
                os = host.get("os", "unknown")

                if method == "Client.OnConnect":
                    logger.info(f"Client {name} ({ip}) [{os}] connected")

                elif method == "Client.OnDisconnect":
                    logger.warning(f"Client {name} ({ip}) [{os}] disconnected")

                self._core.send(
                    event="snapcast_state_updated",
                    method=method,
                    params=params,
                )
                    
        except asyncio.CancelledError:
            logger.debug("Notification listener cancelled")

        except (websockets.exceptions.ConnectionClosed, 
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK) as e:
            logger.debug(f"WebSocket connection closed: {e}")    

        except Exception as e:
            logger.error(f"Notification listener error: {e}")

        finally:
            if self._server_ws:
                await self._server_ws.close()
                self._server_ws = None
