import asyncio
import logging
import threading
import time
import evdev

from core.actor import Actor
from core.types import GpioActions

logger = logging.getLogger(__name__)

DEBOUNCE = 0.2

#creative cd-rom remote temporary
remote_mapping = {
    0x21ac08: GpioActions.VOLUME_UP,
    0x21ac28: GpioActions.VOLUME_DOWN,
    0x21ac30: GpioActions.MUTE,
    0x21ac68: GpioActions.STANDBY,
    0x21ac50: GpioActions.UP,
    0x21ac48: GpioActions.DOWN,
    0x21ac70: GpioActions.SELECT,
    0x21acb0: GpioActions.BACK,
    0x21acd0: GpioActions.DIRECTORY,
    0x21ac10: GpioActions.VISUALISER,
    0x21ac40: GpioActions.PLAY_PAUSE,
    0x21ac80: GpioActions.PLAY_PAUSE,
    0x21acc0: GpioActions.STOP,
    0x21ace0: GpioActions.NEXT,
    0x21aca0: GpioActions.PREVIOUS,
    # 0x21ac68: GpioActions.MEMORY,
    0x21ac20: GpioActions.SOURCE,
    # 0x21ac68: GpioActions.EQUALISER,
    0x21ac90: GpioActions.NOW_PLAYING,
}

class InfraredExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._ir_device = None
        self._last_time = 0
        self._thread = None
        self._stop_event = threading.Event()
        self._loop = None
        self._volume = 0
        self._mute = False

    async def on_start(self):
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            if "gpio_ir" in device.name.lower():
                self._ir_device = device
                break

        if not self._ir_device:
            logger.error("No IR device found")
            return

        logger.info(f"IR device found: {self._ir_device.name}")
        self._loop = asyncio.get_event_loop()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        try:
            for event in self._ir_device.read_loop():
                if self._stop_event.is_set():
                    break
                if event.type == evdev.ecodes.EV_MSC:
                    code = event.value
                    current_time = time.time()
                    if (current_time - self._last_time) > DEBOUNCE:
                        self._last_time = current_time
                        action = remote_mapping.get(code)
                        if action:
                            asyncio.run_coroutine_threadsafe(
                                self._handle_action(action), self._loop
                            )
                        else:
                            logger.debug(f"Unmapped IR code: 0x{code:x}")
        except Exception as e:
            if not self._stop_event.is_set():
                logger.error(f"IR read loop error: {e}")

    async def _handle_action(self, action):
        self._core.send(target=["gpio"], event="ir_received", action=action)

    async def on_event(self, message):
        pass

    async def on_stop(self):
        self._stop_event.set()
        if self._ir_device:
            self._ir_device.close()
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Stopped")