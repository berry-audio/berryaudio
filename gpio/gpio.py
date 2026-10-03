import logging
import asyncio
import RPi.GPIO as GPIO

from core.actor import Actor
from core.types import Command, EncoderMode
from .mcp23017 import GpioMCP23017

logger = logging.getLogger(__name__)

PINS = {17: Command.UP, 27: Command.DOWN,
        22: Command.SELECT, 5: Command.BACK, 6: Command.RIGHT}
REPEAT = {Command.UP, Command.DOWN}
BOUNCE_MS = 20
REPEAT_DELAY = 0.3
REPEAT_INTERVAL = 0.1
LONG_PRESS_TIME = 1.0

PIN_POWER = 0
PIN_DISPLAY = 1
PIN_BACK = 2
PIN_DIRECTORY = 3
PIN_INPUT = 4
PIN_SELECT = 5

PIN_CLK = 1
PIN_DT = 0

LONG_PRESS_MAPPING = {
    Command.LEFT: Command.LEFT_LONG,
    Command.RIGHT: Command.RIGHT_LONG,
    Command.SELECT: Command.SELECT_LONG,
    Command.BACK: Command.BACK_LONG,
}


class GpioExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._mode = "PI"
        self._device = None
        self._loop = None
        self._encoder_mode = EncoderMode.VOLUME
        self._pins = dict(PINS)
        self._repeat = set(REPEAT)
        self._bounce_ms = BOUNCE_MS
        self._repeat_delay = REPEAT_DELAY
        self._repeat_interval = REPEAT_INTERVAL
        self._timers = {}
        self._long_timers = {}

    async def on_config_update(self, config):
        pass

    async def on_event(self, message):
        pass

    async def on_start(self):
        self._loop = asyncio.get_running_loop()
        if self._mode == "MCP23017":
            self._init_mcp()
        else:
            self._init_pi()
        logger.info("Started")

    async def on_stop(self):
        for timer in self._timers.values():
            timer.cancel()
        self._timers.clear()

        for timer in self._long_timers.values():
            timer.cancel()
        self._long_timers.clear()

        if self._mode == "PI":
            for pin in self._pins:
                GPIO.remove_event_detect(pin)
            GPIO.cleanup(list(self._pins))
        elif self._device is not None:
            self._device.close()
        logger.info("Stopped")

    def _init_mcp(self):
        buttons = [
            (Command.STANDBY, PIN_POWER),
            (Command.VISUALISER, PIN_DISPLAY),
            (Command.BACK, PIN_BACK),
            (Command.DIRECTORY, PIN_DIRECTORY),
            (Command.SOURCE, PIN_INPUT),
            (Command.SELECT, PIN_SELECT),
        ]
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

    def _init_pi(self):
        GPIO.setmode(GPIO.BCM)
        for pin in self._pins:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                pin, GPIO.BOTH, callback=self._on_edge, bouncetime=self._bounce_ms
            )

    def _on_edge(self, pin):
        pressed = GPIO.input(pin) == GPIO.LOW
        self._loop.call_soon_threadsafe(
            self._on_pi_gpio, self._pins[pin], pressed)

    def _on_pi_gpio(self, command, pressed):
        if command in LONG_PRESS_MAPPING:
            if pressed:
                self._long_timers[command] = self._loop.call_later(
                    LONG_PRESS_TIME, self._long_fire, command)
            else:
                timer = self._long_timers.pop(command, None)
                if timer:
                    timer.cancel()
                    self._send_command(command)
            return

        self._cancel_repeat(command)
        if not pressed:
            return
        self._send_command(command)
        if command in self._repeat:
            self._timers[command] = self._loop.call_later(
                self._repeat_delay, self._repeat_tick, command)

    def _long_fire(self, command):
        self._long_timers.pop(command)
        self._send_command(LONG_PRESS_MAPPING[command])

    def _repeat_tick(self, command):
        self._send_command(command)
        self._timers[command] = self._loop.call_later(
            self._repeat_interval, self._repeat_tick, command
        )

    def _cancel_repeat(self, command):
        timer = self._timers.pop(command, None)
        if timer:
            timer.cancel()

    def _send_command(self, command):
        self._loop.create_task(self._press_event(command))

    def on_set_encoder_mode(self, mode=EncoderMode.VOLUME):
        logger.debug(f"Encoder mode is '{mode}'")
        self._encoder_mode = mode

    def on_encoder(self, direction):
        if self._encoder_mode == EncoderMode.VOLUME:
            _action = Command.VOLUME_UP if direction == "CW" else Command.VOLUME_DOWN
        elif self._encoder_mode == EncoderMode.DIRECTION:
            _action = Command.DOWN if direction == "CW" else Command.UP
        asyncio.run_coroutine_threadsafe(
            self._press_event(_action), self._loop)

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
