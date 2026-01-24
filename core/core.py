import asyncio
import importlib
import yaml
import logging

from pathlib import Path
from collections import defaultdict
from core.db import DBConnection

logger = logging.getLogger(__name__)


class Core:
    def __init__(self):
        self.db = DBConnection()
        self.extensions = []
        self.routes = defaultdict(list)
        self.tasks = []
        self._responses = {}
        self._loop = asyncio.get_running_loop()

    async def load_extensions_by_name(self, extension_names):
        extensions_to_start = []
        loaded_extensions = []

        # Init Extensions config in database
        for name in extension_names:
            module = importlib.import_module(name)
            ext_class = getattr(module, "Extension")
            loaded_extensions.append((name, ext_class))

            ext_folder = Path(module.__file__).parent
            config_path = ext_folder / "config.yaml"

            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {}

            self.db.init_extension(name, config)

        # Load & Run Extensions 
        for name, ext_class in loaded_extensions:
            config = self.db.get_config()

            ext = ext_class(name=name, core=self, db=self.db, config=config)
            ext.set_loop(self._loop)
            ext._module_name = name

            self.extensions.append(ext)
            self.routes[name].append(ext)
            extensions_to_start.append(ext)

            task = asyncio.create_task(ext.run())
            self.tasks.append(task)

    async def send_to(self, name: str, message):
        for ext in self.extensions:
            if ext.__class__.__name__.lower().startswith(name.lower()):
                await ext.send(message)

    def send(self, *, target: str | list[str] | None = None, **kwargs):
        if target is None:
            targets = self.extensions
        else:
            if isinstance(target, str):
                target = [target]

            targets = {ext for name in target for ext in self.routes.get(name, [])}

        msg = dict(kwargs)

        for ext in targets:
            ext.send(msg)

    def is_callable(self, full_method: str) -> bool:
        if "." not in full_method:
            raise ValueError("Method must be in form 'extension.method'")
        ext_name, method_name = full_method.split(".", 1)
        for ext in self.extensions:
            if ext.__class__.__name__.lower().startswith(ext_name.lower()):
                handler = getattr(ext, f"on_{method_name}", None)
                if not callable(handler):
                    return False
                if asyncio.iscoroutinefunction(handler):
                    return True
                else:
                    return True
        return False

    def _request(self, full_method, **params):
        if self._loop is None or self._loop.is_closed():
            return
        try:
            self._loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self.request(full_method, **params))
            )
        except RuntimeError:
            pass

    async def request(self, full_method, **params):
        logger.debug(f"Requested {full_method} params={params}")
        if "." not in full_method:
            raise ValueError("Method must be in form 'extension.method'")

        ext_name, method_name = full_method.split(".", 1)
        for ext in self.extensions:
            if ext.__class__.__name__.lower().startswith(ext_name.lower()):
                handler = getattr(ext, f"on_{method_name}", None)

                if not callable(handler):
                    logger.warning(
                        f"Method {method_name} not found in extension {ext_name}"
                    )
                    return

                if asyncio.iscoroutinefunction(handler):
                    return await handler(**params)
                else:
                    return handler(**params)
        logger.error(f"Extension {ext_name} not found")
        return

    async def handle_response(self, message_id, response):
        if message_id in self._responses:
            self._responses[message_id].set_result(response)

    async def stop_all(self):
        for ext in self.extensions:
            await ext.on_stop()

        if self.db:
            try:
                self.db.close()
            except Exception as e:
                logger.error(f"Error closing database: {e}")
