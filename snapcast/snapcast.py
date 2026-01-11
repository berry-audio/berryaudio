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
DISCOVERY_TIME = 2

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
        self._local_hostname = socket.gethostname()
        self._proc_snapclient = None
        self._proc_snapserver = None
        self._prev_server = None
        self._server = None
        self._server_ws = None
        self._server_notification_task = None
        self._server_list = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._device = self._config["playback"]["output_device"]
        self.servers = {}
        self.jsonrpc_timeout = 5
        self._connected = False
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
        self._zc_tasks = set()

    async def on_start_service(self):
        await self._core.request("playback.set_metadata", tl_track=self._tl_track)
        return True
    

    async def on_stop_service(self):
        await self._core.request("playback.clear")
        await self._stop_snapclient()
        await self._init_snapserver()
        return True


    """Zeroconf default callbacks"""

    def remove_service(self, **kwargs):
        task = asyncio.create_task(self._service_handler(kwargs))
        self._zc_tasks.add(task)
        task.add_done_callback(self._zc_tasks.discard)

    async def _service_handler(self,kwargs):
        service_state = str(kwargs.get('state_change'))
        service_name = kwargs.get("name")
        
        if service_state == 'ServiceStateChange.Added':
            if service_name not in self.servers:
                await self._handle_service(kwargs)

            if service_name in self.servers:    
                if self.servers[service_name]['status'] == 'unavailable':
                    status = await self.on_get_status(self.servers[service_name]['ip'])
                    if status:
                        stream_status = (
                            status.get("server", {})
                                .get("streams", [{}])[0]
                                .get("status")
                        )
                        self.servers[service_name]['connected'] = self.servers[service_name]['ip'] == self._server
                        self.servers[service_name]['status'] = stream_status
                    self._core.send(event="snapcast_added", server=self.servers[service_name])
                    logger.info(f"Snapcast added server '{service_name}'")
            
        if service_state == 'ServiceStateChange.Removed':
            if service_name in self.servers:
                if self.servers[service_name]['status'] != 'unavailable':
                    self.servers[service_name]['status'] = 'unavailable'
                    self.servers[service_name]['connected'] = False
                    self._core.send(event="snapcast_removed", server=self.servers[service_name])
                    logger.warning(f"Snapcast removed server '{service_name}'")
                    await self._send_state_update()
                    self.servers.pop(service_name)
                    self._server_list = list(self.servers.values())     
                        


    async def _handle_service(self, kwargs):
        try:
            service_type = kwargs.get("service_type")
            service_name = kwargs.get("name")

            if not service_type or not service_name:
                return

            info = await self.zeroconf.async_get_service_info(service_type, service_name)

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

            if self._local_hostname == hostname:
                return

            self.servers[service_name] = {
                "service_name": service_name,
                "name": hostname,
                "ip": ips[0],
                "port": info.port,
                "connected": False,
                "status": 'unavailable',
            }

        except NotRunningException:
            pass         


    """Snapcast functions"""

    async def _connect(self, ip):
        if not ip:
            raise RuntimeError("Invalid or no IP address defined")
        
        await self._disconnect()
        self._reader, self._writer = await asyncio.open_connection(ip, JSONRPC_PORT)
            

    async def _disconnect(self):
        """Properly close the connection"""
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


    async def _send_request(self, request):
        self._writer.write((json.dumps(request) + "\n").encode())
        await self._writer.drain()
        try:
            response = await asyncio.wait_for(self._reader.readline(), timeout=0.1)
            if response:
                result = json.loads(response.decode())
                if "error" in result:
                    print("Snapcast error:", result["error"])
                return result.get("result")
        except asyncio.TimeoutError:
            return None


    async def _get_reverse_dns(self, ip):
        try:
            hostname, _, _ = await self._loop.run_in_executor(None, socket.gethostbyaddr, ip)
            return hostname
        except Exception:
            return None


    async def _send_source_update(self, ip):
        self._source.state.name = await self._get_reverse_dns(ip)
        await self._core.request("source.update_source", source=self._source)    


    async def _send_state_update(self):
        status = await self.on_get_status()
        self._core.send(event="snapcast_state_changed", server=status.get('server'))


    async def _send_connection_update(self, ip):
        servers = await self.on_servers(rescan=False)

        for server in servers:
            if server.get("ip") == ip:
                if self._connected:
                    self._core.send(event="snapcast_connected", server=server)
                    logger.info(f"Snapcast connected to {self._server}:{AUDIO_PORT}")
                else:
                    self._core.send(event="snapcast_disconnected", server=server)
                    logger.warning(f"Snapcast disconnected")       



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

        AsyncServiceBrowser(
            self.zeroconf.zeroconf,
            SERVICE_TYPE,
            handlers=[
                self.remove_service,
            ],
        )
        
        await self._init_snapserver()
        logger.info("Started")


    async def on_event(self, message):
        pass


    async def on_stop(self):
        await self.zeroconf.async_close()
        await self._stop_snapserver()
        await self._stop_snapclient()
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

            async def _on_connected():
                await self._start_notification_listener()
                await self._send_connection_update(self._server)
                await self._send_state_update()     

            def _log(stream, label):
                for line in iter(stream.readline, ""):
                    logger.debug(line.strip())

                    if "successfully established" in line:
                        self._loop.call_soon_threadsafe(
                            asyncio.create_task, _on_connected()
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
            self._connected = False
            self._server = None

            logger.info(f"Snapcast client stopped")


    async def _init_snapclient(self, ip):
        """Snapcast client initialization"""

        await self._stop_snapclient()

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

        self._server = ip
        self._prev_server = ip

        async def _on_connected():
            await self._start_notification_listener()
            await self._send_connection_update(self._server)
            await self._send_source_update(self._server)
            await self._send_state_update() 
        
        async def _on_disconnected():
            await self._stop_notification_listener()
            await self._send_connection_update(self._prev_server)
            await self._send_source_update(self._prev_server)

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
                    self._server = self._prev_server
                    self._source.state.icon = 'speaker'
                    self._source.state.connected = True
                    self._source.state.address = ip
                    self._connected = True

                    self._loop.call_soon_threadsafe(
                        asyncio.create_task, self._stop_snapserver()
                    )

                    self._loop.call_soon_threadsafe(
                        asyncio.create_task, _on_connected()
                    )

                # Connection failed
                if "Failed to connect to host" in line:
                    self._source.state.connected = False

                    if self._connected:
                        self._connected = False
                        self._server = None

                        self._loop.call_soon_threadsafe(
                            asyncio.create_task, _on_disconnected()
                        )

            stream.close()

        threading.Thread(
            target=_log, args=(self._proc_snapclient.stdout, "STDOUT"), daemon=True
        ).start()

        threading.Thread(
            target=_log, args=(self._proc_snapclient.stderr, "STDERR"), daemon=True
        ).start()


    """api callbacks methods"""

    async def on_servers(self, rescan: bool = False):
        if rescan:
            logger.info("Discovering Snapcast servers via Avahi (mDNS)...")
            await asyncio.sleep(DISCOVERY_TIME)

        self._server_list = list(self.servers.values())

        servers = []
        for server in self._server_list:
            server["connected"] = self._server == server.get("ip")
            server["status"] = "unavailable"

            status = await self.on_get_status(server.get("ip"))
            if status:
                stream_status = (
                    status.get("server", {})
                        .get("streams", [{}])[0]
                        .get("status")
                )
                server["status"] = stream_status
            servers.append(server)

        self._server_list = servers
        if rescan:
            logger.info(f"Found ({len(self._server_list)}) Snapcast Servers.")
            logger.debug(self._server_list)
            
        return self._server_list

            
    async def on_disconnect(self):
        await self._stop_snapclient()
        await self._send_connection_update(self._prev_server)

        self._source.state.connected = False
        self._source.state.name = None
        self._source.state.icon = None
        self._source.state.address = None
        await self._core.request("source.update_source", source=self._source) 

        await self._send_state_update()

        self._server = None
        self._prev_server = None
        await self._init_snapserver()
        return True


    async def on_connect(self, ip):
        if not ip:
            raise RuntimeError(f"Invalid or no IP address defined")
        
        await self._core.request("playback.clear")
        await self._core.request("source.set", type='snapcast')
        await self._init_snapclient(ip)
        return True


    async def on_get_status(self, ip=None):
        server = ip or self._server

        if not server:
            return {}

        request = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "Server.GetStatus",
        }
    
        try:
            await self._connect(server)
            result = await self._send_request(request)
            
        except (OSError, ConnectionError, TimeoutError, asyncio.TimeoutError) as exc:
            return {}

        await self._disconnect()

        if not result:
            return {}

        host = result.get("server", {}).get("server", {}).get("host")
        if host:
            host["ip"] = server

        return result


    async def on_set_volume(self, client_id, volume=None, mute=False):
        if not self._server:
            raise RuntimeError(f"Not connected to Snapcast server")

        if not client_id:
            raise RuntimeError("client id not specified")
      
        request = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "Client.SetVolume",
            "params": {
                "id": client_id, 
                "volume": {
                    "muted": mute, 
                    "percent": volume
                    }
                },
        }
        await self._connect(self._server)
        return await self._send_request(request)


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
            
            logger.info("Notification websocket connected")
            
            async for message in self._server_ws:
                msg = json.loads(message)
                method = msg.get("method")
                params = msg.get("params")

                if not method or not params:
                    return

                client = params.get("client", {})
                host = client.get("host", {})
                name = host.get("name", self._local_hostname)
                ip = host.get("ip", self._server)
                os = host.get("os", "unknown")
                
                if method == "Client.OnConnect":
                    logger.info(f"Client {name} ({ip}) [{os}] connected")

                elif method == "Client.OnDisconnect":
                    logger.warning(f"Client {name} ({ip}) [{os}] disconnected")

                elif method == "Stream.OnUpdate":
                    logger.info(f"Client {name} ({ip}) [{os}] stream status changed")

                self._core.send(
                        event="snapcast_notification",
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
