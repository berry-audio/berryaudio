import asyncio
import importlib
import logging
import json

from pathlib import Path
from graphlib import CycleError, TopologicalSorter
from collections import defaultdict
from core.db import DBConnection

logger = logging.getLogger(__name__)
EXTENSIONS_DIR = Path(__file__).resolve().parent.parent

class Core:
    def __init__(self):
        self.db = DBConnection()
        self.extensions = []
        self.routes = defaultdict(list)
        self.tasks = []
        self._responses = {}
        self._loop = asyncio.get_running_loop()

    def load_order(self, manifests):
        manifests = dict(manifests)
        changed = True
        while changed:
            changed = False
            for name, manifest in list(manifests.items()):
                missing = set(manifest.get("depends_on", [])) - manifests.keys()
                if missing:
                    logger.error(
                        f"{name} depends on {sorted(missing)}, which are not "
                        f"available; skipping {name}"
                    )
                    del manifests[name]
                    changed = True
 
        graph = {n: set(m.get("depends_on", [])) for n, m in manifests.items()}
        sorter = TopologicalSorter(graph)
        try:
            sorter.prepare()
        except CycleError as e:
            logger.error(f"Circular depends_on between extensions: {e.args[1]}")
            raise
 
        order = []
        while sorter.is_active():
            ready = sorted(sorter.get_ready())
            order.extend(ready)
            sorter.done(*ready)
        return order

    def load_manifests(self):
        manifests = {}
        for path in sorted(EXTENSIONS_DIR.glob("*/manifest.json")):
            try:
                manifest = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                logger.exception(f"Invalid manifest, skipping: {path}")
                continue
 
            name = manifest.get("name")
            if name != path.parent.name:
                logger.error(
                    f"Manifest name {name!r} does not match folder "
                    f"{path.parent.name!r}, skipping"
                )
                continue
            if manifest.get("enabled", True) is False:
                logger.warning(f"Extension {name} is disabled")
                continue
 
            manifests[name] = manifest
        return manifests
    
    async def load_extensions(self):
        manifests = self.load_manifests()
        config = self.db.reconcile_configs(
            {name: m.get("config") or {} for name, m in manifests.items()}
        )
 
        loaded = set()
        for name in self.load_order(manifests):
            failed = [d for d in manifests[name].get("depends_on", []) if d not in loaded]
            if failed:
                logger.error(f"Skipping {name}: dependencies failed to load: {failed}")
                continue
 
            try:
                module = importlib.import_module(name)
                ext = module.Extension(
                    name=name, core=self, db=self.db, config=config
                )
                ext.set_loop(self._loop)
                ext._module_name = name
                self.extensions.append(ext)
                self.routes[name].append(ext)
                self.tasks.append(asyncio.create_task(ext.run()))
                loaded.add(name)
            except Exception:
                logger.exception(f"Failed to load extension {name}")
                continue
 
            await asyncio.sleep(0)

    
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
        logger.debug(f"Extension {ext_name} not found or disabled")
        return

    async def handle_response(self, message_id, response):
        if message_id in self._responses:
            self._responses[message_id].set_result(response)

    async def stop_all(self):
        for ext in reversed(self.extensions):
            try:
                await ext.on_stop()
            except Exception as e:
                logger.error(f"Error in {ext._module_name}.on_stop: {e}")

        for ext in reversed(self.extensions):
            try:
                await ext.stop()
            except Exception as e:
                logger.error(f"Error stopping {ext._module_name}: {e}")

        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
            self.tasks.clear()

        if self.db:
            try:
                self.db.close()
            except Exception as e:
                logger.error(f"Error closing database: {e}")
