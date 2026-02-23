import logging
import asyncio
from core.actor import Actor
from .mcp23017 import GpioMCP23017

logger = logging.getLogger(__name__)

# Pin definitions A
PIN_POWER = 0
PIN_DISPLAY = 1
PIN_SELECT = 2
PIN_DIRECTORY = 3
PIN_INPUT = 4

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
        self._device = GpioMCP23017(address=0x20, interrupt_pin=23)
        self._loop = asyncio.get_running_loop()

    async def on_config_update(self, config):
        pass

    async def on_event(self, message):
        pass

    async def on_start(self):
        buttons = [
            ("power", PIN_POWER),
            ("display", PIN_DISPLAY),
            ("select", PIN_SELECT),
            ("directory", PIN_DIRECTORY),
            ("source", PIN_INPUT),
        ]
        
        for name, pin in buttons:
            self._device.add_button(name, pin, callback=lambda n=name: self.send_event(n), long_press_callback=lambda n=name: self.send_event_long(n))
        
        self._device.add_encoder("VOLUME", clk_pin=PIN_CLK, dt_pin=PIN_DT, callback=self.on_encoder)
        logger.info("Started")

    async def on_stop(self):
        self._device.close()
        logger.info("Stopped")

    def send_event(self, key):
        self._core.send(target=["web", "display"], event="gpio_state_changed", key=key)

    def send_event_long(self, key):
        self._core.send(target=["web", "display"], event="gpio_state_changed", key=f"{key}_long")

    def on_encoder(self, direction):
        key = "up" if direction == "CW" else "down"
        self.send_event(key)