import logging

from collections import namedtuple
from core.actor import Actor, SourceActor
from core.models import Source
from core.types import PlaybackState
from core.models import RefType

logger = logging.getLogger(__name__)

class SourceExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._current = Source(
            name=None, uri=None, type=None, controls=[], state={"connected": False}
        )

    async def on_start(self):
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

    def on_directory(self):
        _dirs = []
        for ext in self._core.extensions:
            if (isinstance(ext, SourceActor)
                    and hasattr(ext, "_source")
                    and isinstance(ext._source, Source)
                    and ext._source.uri is not None):
                ext._source.active = self._current.uri == ext._source.uri
                _dirs.append(ext._source)
        return _dirs

    def on_update_source(self, source: object) -> None:
        """Updates source information from renderers"""
        if self._current.uri == source.uri:
            self._current = source
            self._core.send(
                target=["web", "display"], event="source_updated", source=self._current
            )

    async def on_set(self, uri: str | None) -> bool:
        """Set the active source and manage start stop services."""
        directory = self.on_directory()
        current_source = next(
            (source for source in directory if source.uri == uri), None
        )

        previous = self._current.uri
        current = uri

        if current is None:
            stop_method = f"{previous}.stop_service"
            if self._core.is_callable(stop_method) and previous is not None:
                if await self._core.request(stop_method):
                    logger.info(f"Stopping {previous} service")

        if current_source is None:
            return

        if current == "playlist" or current == "multiroom" or current == "settings":
            return

        if current == previous:
            return
        
        uris = [source.uri for source in directory] 

        if current is not None and current in uris: 
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

        if uri is not None:
            if self._core.is_callable(start_method):
                logger.info(f"Starting {current} service")
                await self._core.request(start_method)
                self._current = Source(
                    name=current_source.name,
                    uri=uri,
                    type=RefType.SOURCE,
                    controls=[],
                    state={"connected": False},
                )
                self._core.send(
                    target=["web", "display"],
                    event="source_changed",
                    source=self._current,
                )
            else:
                logger.error(f"Failed to start service for source {current}")
                raise RuntimeError(f"Failed to start service for source {current}")
        else:
            self._current = Source(
                name=None,
                uri=uri,
                type=RefType.SOURCE,
                controls=[],
                state={"connected": False},
            )
            self._core.send(
                target=["web", "display"], event="source_changed", source=self._current
            )

        return True

    def on_get(self) -> dict:
        """Return the currently active source."""
        return self._current
