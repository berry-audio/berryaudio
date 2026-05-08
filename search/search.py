import logging
import asyncio

from core.actor import Actor

logger = logging.getLogger(__name__)


class SearchExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config

    async def on_start(self):
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

    async def on_search(self, query):
        results = await asyncio.gather(
            self._core.request("radio.search", query=query),
            self._core.request("local.search", query=query),
            return_exceptions=True,
        )
        result_merged = {}
        for result in results:
            if isinstance(result, Exception):
                continue
            if isinstance(result, dict):
                for key, value in result.items():
                    if len(value):
                        result_merged[key] = value
        return result_merged
