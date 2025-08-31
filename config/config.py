import logging
from core.actor import Actor

logger = logging.getLogger(__name__)

class ConfigExtension(Actor):
    def __init__(self, core, db, config):
        super().__init__()
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
        hostname = config.get('system',{}).get('hostname', None)
        if hostname:
            await self._core.request("system.set_hostname", hostname=hostname)
        logger.info(config)
        self._db.set_config(config)
        return True

    def on_get(self):
        return self._db.get_config()