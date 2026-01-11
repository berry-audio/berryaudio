import logging
from core.actor import Actor
from core.models import Source
from core.types import PlaybackState

logger = logging.getLogger(__name__)

SOURCES = {
    None,
    "local", 
    "storage", 
    "radio", 
    "bluetooth", 
    "shairportsync", 
    "spotify",
    "snapcast"
    }

class SourceExtension(Actor):
    def __init__(self, core, db, config):
        super().__init__()
        self._core = core
        self._db = db
        self._source = Source(type=None, controls=[], state={'connected': False}) 


    async def on_start(self):
        logger.info("Started")


    async def on_event(self, message):
        pass


    async def on_stop(self):
        logger.info("Stopped")


    def on_update_source(self, source : object) -> None:
        """Updates source information from renderers"""
        if self._source.type == source.type:
            self._source = source
            self._core.send(event="source_updated", source=self._source)


    async def on_set(self, type: str | None) -> bool:
        """Set the active source and manage start stop services."""
        previous = self._source.type
        current = type

        if current == previous:
            return True

        if current in SOURCES:
            start_method = f"{current}.start_service"
            stop_method = f"{previous}.stop_service"

            if self._core.is_callable(stop_method) and previous is not None:
                if await self._core.request(stop_method):
                    logger.info(f"Stopping {previous} service")
                else:
                    logger.error(f"Failed to stop service for source {previous}")
                    raise RuntimeError(f"Failed to stop service for source {previous}")
        else:
            if current is not None:
                logger.error(f"Unknown {current} source type")
                raise ValueError(f"Unknown {current} source type")
     
        if type is not None:
            if self._core.is_callable(start_method):
                logger.info(f"Starting {current} service")
                await self._core.request(start_method)
                self._source = Source(type=type, controls=[], state={'connected': False}) 
                self._core.send(event="source_changed", source=self._source)
            else:
                logger.error(f"Failed to start service for source {current}")
                raise RuntimeError(f"Failed to start service for source {current}")    
        else:
            self._source = Source(type=type, controls=[], state={'connected': False}) 
            self._core.send(event="source_changed", source=self._source)

        return True


    def on_get(self) -> dict:
        """Return the currently active source."""
        return self._source
