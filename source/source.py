import logging

from core.actor import Actor, SourceActor
from core.models import Source

logger = logging.getLogger(__name__)


class SourceExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._current = Source(
            name=None, uri=None, controls=[], state={"connected": False}
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
            if (
                isinstance(ext, SourceActor)
                and hasattr(ext, "_source")
                and isinstance(ext._source, Source)
                and ext._source.uri is not None
            ):
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

    async def on_set(self, uri: str | None = None) -> bool:
        """Set the active source and manage start stop services."""
        uri_prev = self._current.uri

        if uri == uri_prev:
            return True

        directory = self.on_directory()
        if uri is not None and uri not in (source.uri for source in directory):
            logger.error(f"Unknown source type: {uri}")
            raise ValueError(f"Unknown source type: {uri}")

        if uri_prev is not None:
            stop_method = f"{uri_prev}.stop_service"
            if self._core.is_callable(stop_method):
                try:
                    logger.debug(f"Stopping {uri_prev} service")
                    await self._core.request(stop_method)
                    self._core.send(
                        target=["web", "display"], event="source_changed", source=Source(
                            name=None,
                            uri=uri,
                            controls=[],
                            state={"connected": False},
                        )
                    )
                except Exception as e:
                    raise

        if uri is None:
            self._current = Source(
                name=None, uri=None, controls=[], state={"connected": False}
            )

        if uri is not None:
            start_method = f"{uri}.start_service"
            if self._core.is_callable(start_method):
                try:
                    logger.debug(f"Starting {uri} service")
                    source = await self._core.request(start_method)
                except Exception as e:
                    self._core.send(
                        target=["web", "display"], event="source_changed", source=Source(
                            name=None,
                            uri=None,
                            controls=[],
                            state={"connected": False},
                        )
                    )
                    raise
                self._current = source
                self._core.send(
                    target=["web", "display"],
                    event="source_changed",
                    source=self._current,
                )
            else:
                logger.error(f"Start service not found for source {uri}")

        self._core.send(
            target=["web", "display"],
            event="options_changed",
            single=False,
            repeat=False,
            shuffle=False,
        )
        return True

    def on_get(self) -> dict:
        """Return the currently active source."""
        return self._current
