import logging
import asyncio

from core.actor import Actor
from core.types import Command, EncoderMode
from .mcp23017 import GpioMCP23017

logger = logging.getLogger(__name__)

# Pin definitions A
PIN_POWER = 0
PIN_DISPLAY = 1
PIN_BACK = 2
PIN_DIRECTORY = 3
PIN_INPUT = 4
PIN_SELECT = 5

# Pin definitions B
PIN_CLK = 1
PIN_DT = 0


class GpioExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._device = "MCP23017"
        self._loop = asyncio.get_running_loop()
        self._encoder_mode = EncoderMode.VOLUME

    async def on_config_update(self, config):
        pass

    async def on_event(self, message):
        pass

    async def on_start(self):
        buttons = [
            (Command.STANDBY, PIN_POWER),
            (Command.VISUALISER, PIN_DISPLAY),
            (Command.BACK, PIN_BACK),
            (Command.DIRECTORY, PIN_DIRECTORY),
            (Command.SOURCE, PIN_INPUT),
            (Command.SELECT, PIN_SELECT),
        ]

        if self._device is not None:
            self._device = GpioMCP23017()

            for name, pin in buttons:
                self._device.add_button(
                    name,
                    pin,
                    callback=lambda n=name: asyncio.run_coroutine_threadsafe(
                        self._press_event(n), self._loop
                    ),
                    long_press_callback=lambda n=name: asyncio.run_coroutine_threadsafe(
                        self._press_long_event(n), self._loop
                    ),
                )

            self._device.add_encoder(
                "VOLUME", clk_pin=PIN_CLK, dt_pin=PIN_DT, callback=self.on_encoder
            )
        logger.info("Started")

    async def on_stop(self):
        if self._device is not None:
            self._device.close()
        logger.info("Stopped")

    def on_set_encoder_mode(self, mode=EncoderMode.VOLUME):
        logger.debug(f"Encoder mode is '{mode}'")
        self._encoder_mode = mode

    def on_encoder(self, direction):
        if self._encoder_mode == EncoderMode.VOLUME:
            _action = Command.VOLUME_UP if direction == "CW" else Command.VOLUME_DOWN
        elif self._encoder_mode == EncoderMode.DIRECTION:
            _action = Command.DOWN if direction == "CW" else Command.UP
        asyncio.run_coroutine_threadsafe(self.send_event(_action), self._loop)

    async def _press_event(self, action):
        self._core.send(
            target=["web", "display", "command"], event="command", action=action
        )

    async def _press_long_event(self, action):
        self._core.send(
            target=["web", "display", "command"],
            event="command",
            action=f"{action}_long",
        )
