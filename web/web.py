import pathlib
import asyncio
import json
import logging
import aiofiles

from aiohttp import web, WSMsgType
from core.actor import Actor
from main import USE_GBULB
from core.actor import Actor
from core.util import handle_json, handle_json_ws

logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

ASSET_MIME_MAP = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
}
IMAGE_MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class WebExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self.ws = None

    async def on_start(self):
        logger.info("Started")
        self._server_task = asyncio.create_task(self.run_server())
        self._clients = set()

    async def stream_file(self, request, file_path: pathlib.Path, content_type: str):
        """Stream a file manually to avoid sendfile (compatible with gbulb)."""
        resp = web.StreamResponse()
        resp.content_type = content_type
        await resp.prepare(request)

        async with aiofiles.open(file_path, "rb") as f:
            chunk = await f.read(64 * 1024)  # 64 KB chunks
            while chunk:
                await resp.write(chunk)
                chunk = await f.read(64 * 1024)

        await resp.write_eof()
        return resp

    def _add_static_route(
        self, prefix: str, directory: pathlib.Path, mime_map: dict = None
    ):
        """Add static file serving for aiohttp, handling USE_GBULB mode."""
        if USE_GBULB:

            async def handler(request):
                filename = request.match_info["filename"]
                file_path = directory / filename
                if not file_path.exists():
                    raise web.HTTPNotFound()
                ext = file_path.suffix.lower()
                content_type = (
                    mime_map.get(ext, "application/octet-stream")
                    if mime_map
                    else "application/octet-stream"
                )
                return await self.stream_file(
                    request, file_path, content_type=content_type
                )

            self._app.router.add_get(f"{prefix}{{filename:.*}}", handler)
        else:
            self._app.router.add_static(prefix, path=directory, name=prefix.strip("/"))

    async def run_server(self):
        host = "0.0.0.0"
        port = 8080
        self._app = web.Application()

        www_dir = pathlib.Path(__file__).parent / "www"
        images_dir = www_dir / "images"

        self._app.router.add_get("/ws", self.websocket_handler)
        self._app.router.add_get("/rpc", self.webrpc_handler)

        async def index_handler(request):
            if USE_GBULB:
                return await self.stream_file(
                    request, www_dir / "index.html", content_type="text/html"
                )
            else:
                return web.FileResponse(
                    www_dir / "index.html", headers={"Content-Type": "text/html"}
                )

        self._app.router.add_get("/{tail:.*}", index_handler)

        self._add_static_route("/assets/", www_dir / "assets", ASSET_MIME_MAP)
        self._add_static_route("/images/", images_dir, IMAGE_MIME_MAP)

        runner = web.AppRunner(self._app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Server running at http://{host}:{port}")

        while self.running:
            await asyncio.sleep(1)
        await runner.cleanup()

    async def safe_send(self, ws, message: dict):
        if ws is None:
            return
        for client in list(self._clients):
            try:
                if not client.closed:
                    await client.send_str(
                        json.dumps(json.loads(handle_json_ws(message)))
                    )
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                self._clients.discard(ws)

    async def webrpc_handler(self, request):
        try:
            data = await request.json()
            response = await self.handle_jsonrpc(None, data, send=False)
        except Exception as e:
            response = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": None,
            }
        return web.json_response(response)

    async def websocket_handler(self, request):
        self.ws = web.WebSocketResponse()
        await self.ws.prepare(request)
        self._clients.add(self.ws)
        logger.info(f"Client connected: {request.remote}")
        try:
            async for msg in self.ws:
                if msg.type == web.WSMsgType.TEXT:
                    await self.handle_jsonrpc(self.ws, msg.data)
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WS error: {self.ws.exception()}")
        finally:
            self._clients.discard(self.ws)
            logger.info(f"Client disconnected: {request.remote}")
        return self.ws

    async def handle_jsonrpc(self, ws, data, send=True):
        try:
            request_obj = json.loads(data) if isinstance(data, str) else data
            if request_obj.get("jsonrpc") != "2.0":
                raise ValueError("Invalid JSON-RPC 2.0 request")

            method = request_obj.get("method")
            params = request_obj.get("params", None)
            req_id = request_obj.get("id")

            if params is None:
                result = await self._core.request(method)
            elif isinstance(params, dict):
                result = await self._core.request(method, **params)
            else:
                raise ValueError("Params must be a JSON object (dict) or null")

            response = json.loads(
                handle_json({"jsonrpc": "2.0", "result": result, "id": req_id})
            )

        except Exception as e:
            response = json.loads(
                handle_json(
                    {
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": str(e)},
                        "id": (
                            request_obj.get("id") if "request_obj" in locals() else None
                        ),
                    }
                )
            )

        if ws and send:
            await self.safe_send(ws, response)
        return response

    async def on_event(self, message):
        await self.safe_send(self.ws, message)
        logger.debug(f"Sending message: {message}")

    async def on_stop(self):
        self.running = False
        if hasattr(self, "_server_task"):
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped")
