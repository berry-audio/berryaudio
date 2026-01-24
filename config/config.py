import logging

from core.actor import Actor

logger = logging.getLogger(__name__)


class ConfigExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config

    async def on_start(self):
        config = self._db.get_config()
        logger.info(config)

    async def on_event(self, message):
        pass

    async def on_stop(self):
        pass

    async def on_set(self, config):
        for ext in config:
            self._core._request(f"{ext}.config_update", config=config)
        self._db.set_config(config)
        logger.info(config)
        return True

    def on_get(self):
        return self._db.get_config()
