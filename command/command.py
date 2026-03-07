import logging

from core.actor import Actor
from core.types import Command

logger = logging.getLogger(__name__)


class CommandExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config

    async def on_config_update(self, config):
        pass

    async def on_event(self, message):
        event = message.get("event")
        if event == "command":
            action = message.get("action")

            if action == Command.STANDBY:
                await self._core.request("system.standby")

            elif action == Command.PLAY_PAUSE:
                await self._core.request("playback.play")

            elif action == Command.STOP:
                await self._core.request("playback.stop")

            elif action == Command.NEXT:
                await self._core.request("playback.next")

            elif action == Command.PREVIOUS:
                await self._core.request("playback.previous")

            elif action == Command.MUTE:
                await self._core.request("mixer.set_mute")

            elif action == Command.VOLUME_UP:
                await self._core.request("mixer.volume_up")

            elif action == Command.VOLUME_DOWN:
                await self._core.request("mixer.volume_down")

    async def on_start(self):
        logger.info("Started")

    async def on_stop(self):
        logger.info("Stopped")
