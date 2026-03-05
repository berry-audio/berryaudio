import asyncio
import logging
import threading
import time
import evdev
import subprocess

from core.actor import Actor
from core.types import Command

logger = logging.getLogger(__name__)

DEBOUNCE = 0.2
IR_PATH = "/usr/bin/ir-keytable"

# creative cd-rom remote temporary
remote_mapping = {
    0x21AC08: Command.VOLUME_UP,
    0x21AC28: Command.VOLUME_DOWN,
    0x21AC30: Command.MUTE,
    0x21AC68: Command.STANDBY,
    0x21AC50: Command.UP,
    0x21AC48: Command.DOWN,
    0x21AC70: Command.SELECT,
    0x21ACB0: Command.BACK,
    0x21ACD0: Command.DIRECTORY,
    0x21AC10: Command.VISUALISER,
    0x21AC40: Command.PLAY_PAUSE,
    0x21AC80: Command.PLAY_PAUSE,
    0x21ACC0: Command.STOP,
    0x21ACE0: Command.NEXT,
    0x21ACA0: Command.PREVIOUS,
    # 0x21ac68: Command.MEMORY,
    0x21AC20: Command.SOURCE,
    # 0x21ac68: Command.EQUALISER,
    0x21AC90: Command.NOW_PLAYING,
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
        self._loop = asyncio.get_event_loop()
        self._volume = 0
        self._mute = False
        self._thread = None
        self._proc = None

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
        self._ir_init()

        if self._proc is not None:
            self._thread = threading.Thread(
                target=self._handle_receive, daemon=True
            ).start()

    def _ir_init(self):
        cmd = [
            "sudo",
            IR_PATH,
            "-c",
            "-p",
            "all",
            "-t",
        ]
        self._proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
        )

        def log(stream, label):
            for line in iter(stream.readline, ""):
                if "warning" in line:
                    logger.warning(line.strip())
            stream.close()

        threading.Thread(
            target=log, args=(self._proc.stdout, "STDOUT"), daemon=True
        ).start()

    async def on_event(self, message):
        pass

    async def on_stop(self):
        if self._thread is not None:
            self._thread.terminate()
            self._thread.kill()

        if self._proc is not None:
            self._proc.terminate()
            self._proc.kill()

        if self._ir_device:
            self._ir_device.close()

        logger.info("Stopped")

    def _handle_receive(self):
        try:
            for event in self._ir_device.read_loop():
                if event.type == evdev.ecodes.EV_MSC:
                    code = event.value
                    current_time = time.time()
                    if (current_time - self._last_time) > DEBOUNCE:
                        self._last_time = current_time
                        action = remote_mapping.get(code)
                        if action:
                            self._core.send(
                                target=["web", "display", "command"],
                                event="command",
                                action=action,
                            )
                            logger.info(f"IR code 0x{code:x} {action}")
                        else:
                            logger.warning(f"Unmapped IR code: 0x{code:x}")
        except Exception as e:
            logger.error(f"IR read loop error: {e}")
