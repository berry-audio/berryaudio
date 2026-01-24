import logging
import psutil
import platform
import socket
import subprocess
import re
import os
import socket
import threading
import netifaces

from datetime import datetime
from zoneinfo import ZoneInfo
from core.actor import Actor

logger = logging.getLogger(__name__)


class SystemExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._thread = None
        self._stop_event = threading.Event()
        self._is_standby = True

    async def on_config_update(self, config):
        updated_config = config[self._name]
        if "hostname" in updated_config:
            self.on_set_hostname(updated_config.get("hostname"))

    async def on_start(self):
        self._thread = threading.Thread(target=self.send_time_update, daemon=True)
        self._thread.start()
        logger.info("Started")

    async def on_stop(self):
        self._stop_event.set()  # signal the thread to stop
        if self._thread:
            self._thread.join()  # wait for it to exit immediately
        logger.info("Stopped")

    async def on_event(self, message):
        pass

    def send_time_update(self):
        while not self._stop_event.is_set():
            self._core.send(
                target="web", event="system_time_updated", datetime=self.on_datetime()
            )
            self._stop_event.wait(timeout=30)

    def on_datetime(self):
        tz = ZoneInfo(self._config["system"]["timezone"])
        now = datetime.now(tz)
        time = now.strftime("%Y-%m-%dT%H:%M:%S")
        return time

    async def on_standby(self, state: bool):
        self._is_standby = state
        self._core.send(
            target="web", event="system_power_state", state=self.on_get_power_state()
        )

        await self._core.request("source.set", type=None)
        await self._core.request("bluetooth.adapter_set_state", state=False)

        if state:
            logger.info("System going into Standby...")
        else:
            logger.info("System wakeup...")
        return True

    def on_get_power_state(self):
        return {"standby": self._is_standby}

    def on_shutdown(self):
        os.system("sudo shutdown -h now")
        return True

    def on_reboot(self):
        os.system("sudo shutdown -r now")
        return True

    def on_set_hostname(self, hostname: str):
        subprocess.run(["sudo", "hostnamectl", "set-hostname", hostname], check=True)
        logger.info(f"Hostname changed to: {hostname}")

    def get_temperature(self):
        try:
            result = subprocess.run(
                ["vcgencmd", "measure_temp"], capture_output=True, text=True
            )
            output = result.stdout.strip()
            match = re.search(r"[\d\.]+", output)
            if match:
                return float(match.group(0))
            return 0
        except FileNotFoundError:
            return 0

    def get_volts(self, target=0):
        try:
            cmd = ["vcgencmd", "measure_volts"]
            if target:
                cmd.append(target)
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout.strip()
            match = re.search(r"[\d\.]+", output)
            if match:
                return float(match.group(0))
            return 0
        except FileNotFoundError:
            return 0

    def get_hardware_model(self):
        try:
            with open("/proc/device-tree/model") as f:
                return f.read().strip()
        except FileNotFoundError:
            pass

        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if (
                        line.startswith("Model")
                        or line.startswith("Hardware")
                        or line.startswith("model name")
                    ):
                        return line.strip()
        except FileNotFoundError:
            pass

        return platform.uname().machine

    def on_info(self):
        system = platform.system()
        machine = platform.machine()
        hostname = socket.gethostname()

        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_cores = psutil.cpu_count(logical=True)

        info = platform.uname()
        version = info.version

        mem = psutil.virtual_memory()
        mem_used = mem.used / (1024**3)
        mem_total = mem.total / (1024**3)
        mem_percent = mem.percent

        disk = psutil.disk_usage("/")
        disk_used = disk.used / (1024**2)
        disk_total = disk.total / (1024**2)
        disk_percent = disk.percent

        system_info = {
            "os": f"{system} ({machine})",
            "hostname": hostname,
            "model": self.get_hardware_model(),
            "software": "1.2.0",
            "version": version,
            "cpu": {
                "volts": self.get_volts("core"),
                "usage_percent": cpu_percent,
                "cores": cpu_cores,
                "temperature": self.get_temperature(),
            },
            "memory": {
                "mem_used": mem_used,
                "mem_total": mem_total,
                "mem_percent": mem_percent,
            },
            "disk": {
                "disk_used": disk_used,
                "disk_total": disk_total,
                "disk_percent": disk_percent,
            },
            "network": {},
        }

        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    system_info["network"][interface] = addr["addr"]

        return system_info
