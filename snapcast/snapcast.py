import logging
import threading
import subprocess
import asyncio
import socket
import os
import socket
import json
import websockets

from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser
from zeroconf._exceptions import NotRunningException
from pathlib import Path
from core.actor import Actor

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_snapcast._tcp.local."
DISCOVERY_TIME = 5

SERVER_WS_PORT = 1780
JSONRPC_PORT = 1705
AUDIO_PORT = 1704

SNAPSERVER_PATH = "/usr/local/bin/snapserver"
SNAPCLIENT_PATH = "/usr/local/bin/snapclient"
SNAPSERVER_CONFIG_PATH = Path(__file__).parent / "snapserver.conf"

DEFAULT_CONFIG = {
    "snapserver" : 0,
    "source_name" : "Loopback",
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
        self._proc = None
        self.servers = {}
        self._server = {}
        self._server_ws = None
        self._server_notification_task = None
        self._device = self._config['playback']['output_device']
        self.jsonrpc_timeout = 1
        self.zeroconf = AsyncZeroconf()


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
        loop = asyncio.get_running_loop()
        try:
            hostname, _, _ = await loop.run_in_executor(None, socket.gethostbyaddr, ip)
            return hostname
        except Exception:
            return None


    async def _get_hostname(self, ip):
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "Server.GetStatus"
            }

            _result = await self._send_request(ip, request, JSONRPC_PORT)
            return _result["server"]["hostname"]
       

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
                info.server.rstrip(".") if info.server else
                await self._get_hostname(ips[0]) or
                await self._get_reverse_dns(ips[0]) or
                "Unknown"
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
        logger.info("Started")
        

    async def on_event(self, message):
        pass


    async def on_stop(self):
        await self.zeroconf.async_close()
        await self._stop_notification_listener()
        self.on_disconnect()
        logger.info("Stopped")


    """api callbacks methods"""

    async def on_servers(self):
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
        

    def on_disconnect(self):
        self._server = {}

        if self._proc is not None:
            self._proc.terminate()
            self._proc.kill()
            self._proc = None
        return True
        
        
    async def on_connect(self, ip, port=AUDIO_PORT):
        if not ip:
            raise RuntimeError(f"Invalid or no IP address defined")    

        self.on_disconnect()

        cmd = [
                SNAPCLIENT_PATH,
                f"tcp://{ip}:{port}",
                "--player",
                "alsa",
                "--soundcard",
                self._device,
            ]
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1 
        )

        def _log(stream, label):
            for line in iter(stream.readline, ''):
                logger.debug(line.strip())
                self._server = {"ip": ip, "port": port}
                if "Connected" in line:
                    self._core.send(event="snapcast_client_connected", server=self._server)
                    self._loop.call_soon_threadsafe(
                        asyncio.create_task,
                        self._start_notification_listener()
                    )

                    logger.info(f"Snapcast client connected {ip}:{port}")
                elif "Failed to connect to host" in line:
                    self._core.send(event="snapcast_client_disconnected", server=self._server)
                    self._server = {}
                    self._loop.call_soon_threadsafe(
                        asyncio.create_task,
                        self._stop_notification_listener()
                    )
                    
                    logger.error(f"Snapcast client failed to connect {ip}:{port}")    
            stream.close()    

        threading.Thread(target=_log, args=(self._proc.stdout, "STDOUT"), daemon=True).start()
        threading.Thread(target=_log, args=(self._proc.stderr, "STDERR"), daemon=True).start()
        return True


    async def on_get_status(self):
        if not self._server.get("ip"):
            return {
                "clients": [],
                "server": {},
                "streams": []
            }
        
        result_build = {}

        request = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "Server.GetStatus"
        }

        _result = await self._send_request(self._server.get("ip"), request, JSONRPC_PORT)
        _server = _result.get("server", {})
        _groups = _server.get("groups", [])

        result_build['clients'] = []
        for group in _groups:
            clients = group.get("clients", [])
            for client in clients:
                result_build['clients'].append(client)
    
        result_build['server'] = _server.get('server')
        result_build['server']['host']['ip'] = self._server.get("ip")
        result_build['streams'] = _server.get('streams')

        return result_build


    async def on_set_volume(self, client_id, volume, mute=False):
        if not self._server.get("ip"):
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
            }
        }

        return await self._send_request(self._server.get("ip"), request, JSONRPC_PORT)


    """Snapcast notification listener functions"""

    async def _stop_notification_listener(self):
        """Stop notification listener"""
        if self._server_ws:
            await self._server_ws.close()
            self._server_ws = None

        if self._server_notification_task:
            self._server_notification_task.cancel()
            self._server_notification_task = None


    async def _start_notification_listener(self):
        """Start notification listener"""
        self._server_notification_task = asyncio.create_task(self._handle_notifications())


    async def _handle_notifications(self):
        self._server_ws = await websockets.connect(
            f"ws://{self._server['ip']}:{SERVER_WS_PORT}/jsonrpc"
        )
        try:
            async for message in self._server_ws:
                msg = json.loads(message)
                self._core.send(event="snapcast_state_updated", method=msg['method'], params=msg['params'])
                
        except asyncio.CancelledError:
            pass
        