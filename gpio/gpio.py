import logging
import asyncio

from core.actor import Actor
from core.types import GpioActions, EncoderMode

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
        self._volume = 0
        self._muted = False
        self._encoder_mode = EncoderMode.VOLUME

    async def on_config_update(self, config):
        pass

    async def on_event(self, message):
        event = message.get("event")
        if event == "ir_received":
            await self.send_event(message.get("action"))

        elif event == "mixer_mute":
            self._muted = message.get("mute")

        elif event == "volume_changed":
            self._volume = message.get("volume")

    async def on_start(self):
        buttons = [
            (GpioActions.STANDBY, PIN_POWER),
            (GpioActions.VISUALISER, PIN_DISPLAY),
            (GpioActions.BACK, PIN_BACK),
            (GpioActions.DIRECTORY, PIN_DIRECTORY),
            (GpioActions.SOURCE, PIN_INPUT),
            (GpioActions.SELECT, PIN_SELECT),
        ]

        if self._device is not None:
            self._device = GpioMCP23017(address=0x20, interrupt_pin=23)

            for name, pin in buttons:
                self._device.add_button(
                    name,
                    pin,
                    callback=lambda n=name: asyncio.run_coroutine_threadsafe(
                        self.send_event(n), self._loop
                    ),
                    long_press_callback=lambda n=name: asyncio.run_coroutine_threadsafe(
                        self.send_event_long(n), self._loop
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

    async def send_event(self, action):
        self._core.send(
            target=["web", "display"], event="gpio_state_changed", key=action
        )

        if action == GpioActions.STANDBY:
            await self._core.request("system.standby")

        elif action == GpioActions.PLAY_PAUSE:
            await self._core.request("playback.play")

        elif action == GpioActions.STOP:
            await self._core.request("playback.stop")

        elif action == GpioActions.NEXT:
            await self._core.request("playback.next")

        elif action == GpioActions.PREVIOUS:
            await self._core.request("playback.previous")

        elif action == GpioActions.MUTE:
            await self._core.request("mixer.set_mute", mute=not self._muted)

        elif action == GpioActions.VOLUME_UP:
            await self._core.request("mixer.volume_up")

        elif action == GpioActions.VOLUME_DOWN:
            await self._core.request("mixer.volume_down")

    async def send_event_long(self, action):
        self._core.send(
            target=["web", "display"], event="gpio_state_changed", key=f"{action}_long"
        )

    def on_set_encoder_mode(self, mode=EncoderMode.VOLUME):
        logger.debug(f"Encoder mode is '{mode}'")
        self._encoder_mode = mode

    def on_encoder(self, direction):
        if self._encoder_mode == EncoderMode.VOLUME:
            _action = (
                GpioActions.VOLUME_UP if direction == "CW" else GpioActions.VOLUME_DOWN
            )
        elif self._encoder_mode == EncoderMode.DIRECTION:
            _action = GpioActions.DOWN if direction == "CW" else GpioActions.UP
        asyncio.run_coroutine_threadsafe(self.send_event(_action), self._loop)
