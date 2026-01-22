import subprocess
import logging
import asyncio
import psutil
import pyudev
import threading

from pathlib import Path
from core.actor import Actor
from core.types import PlaybackControls
from core.util.metadata import Metadata
from core.models import Image, Album, Artist, Track, Source
from .storage_utils import get_storage_info, list_paths

logger = logging.getLogger(__name__)


class StorageExtension(Actor):
    def __init__(self, core, db, config):
        super().__init__()
        self._core = core
        self._metadata = Metadata("storage")
        self._proc_mount = None
        self._proc_unmount = None
        self._storages = get_storage_info()
        self._source = Source(
            type="storage",
            controls=[
                PlaybackControls.SEEK,
                PlaybackControls.PLAY,
                PlaybackControls.PAUSE,
                PlaybackControls.NEXT,
                PlaybackControls.PREVIOUS,
                PlaybackControls.REPEAT,
                PlaybackControls.SHUFFLE,
            ],
            state={},
        )

    async def on_start(self):
        threading.Thread(target=self.monitor_usb, daemon=True).start()
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        await asyncio.sleep(0.2)
        logger.info("Stopped")
        return True

    async def on_start_service(self):
        return True

    async def on_stop_service(self):
        await self._core.request("playback.clear")
        return True

    def _build_ref(self, uri: str) -> dict:
        cover_path, tags = self._metadata.extract_cover_and_tags(uri)  # id is full path
        obj: dict = {
            "uri": f"storage:{uri}",
            "images": [Image(uri=cover_path or "")],
            "artists": frozenset(),
            "albums": frozenset(),
            "composers": frozenset(),
            "performers": frozenset(),
        }

        if tags.get("name"):
            obj["name"] = tags["name"]
        if tags.get("genre"):
            obj["genre"] = tags["genre"]
        if tags.get("date"):
            obj["date"] = tags["date"]
        if tags.get("disc_number"):
            obj["disc_no"] = tags["disc_number"]
        if tags.get("track_number"):
            obj["track_no"] = tags["track_number"]
        if tags.get("length"):
            obj["length"] = int(tags["length"])
        if tags.get("bitrate"):
            obj["bitrate"] = tags["bitrate"]

        if tags.get("album"):
            album = Album(
                uri=None, name=tags["album"], date=tags.get("date"), images=None
            )
            obj["albums"] = frozenset([album])

        if tags.get("artist"):
            obj["artists"] = frozenset(
                [Artist(uri=None, name=tags["artist"], images=None)]
            )
        return obj

    async def on_playback_uri(self, id: str) -> any:
        self._core._request("source.update_source", source=self._source)
        uri = Path(id).as_uri()
        return f"{uri}" if id else None

    async def on_lookup_track(self, id: str) -> Track:
        return Track(**self._build_ref(id))

    async def on_list(self):
        return get_storage_info()

    def on_mount(self, dev: str):
        return self.mount_devices(dev)

    def on_unmount(self, dev: str):
        return self.unmount_device(dev)

    def on_info(self, dev: str) -> dict | None:
        for section in ("mounted", "unmounted"):
            data = get_storage_info()
            for item in data.get(section, []):
                if item.get("dev") == dev:
                    return item
        return False

    def on_dir(self, path: str):
        return list_paths(
            path,
            extensions=[
                ".mp3",
                ".m4a",
                ".flac",
                ".wav",
                ".ogg",
                ".dsf",
                ".m3u",
                ".m3u8",
            ],
        )

    def is_internal(self, dev_node):
        if "/dev/mmcblk0p1" in dev_node or "/dev/mmcblk0p2" in dev_node:
            logger.warning("Cannot mount/unmount internal storage")
            return True
        return False

    def mount_device(self, dev_node):
        if not self.is_internal(dev_node):
            logger.debug(f"Mounting {dev_node}...")
            try:
                self._proc_mount = subprocess.run(
                    ["udisksctl", "mount", "-b", dev_node],
                    text=True,
                    capture_output=True,
                )
                logger.debug(self._proc_mount.stdout.strip())

                mount_point = None
                for line in self._proc_mount.stdout.splitlines():
                    if "Mounted" in line:
                        mount_point = line.split(" at ")[1].rstrip(".")
                if mount_point:
                    usage = psutil.disk_usage(mount_point)
                    self._core.send(
                        target="web",
                        event="storage_updated",
                        storage=self.on_info(dev_node),
                    )
                    logger.debug(
                        f"Mounted at {mount_point} - Total: {usage.total}, "
                        f"Used: {usage.used}, Free: {usage.free}"
                    )
                return mount_point
            except Exception as e:
                logger.error(f"Error mounting {dev_node}: {e}")
                return False

    def unmount_device(self, dev_node):
        if not self.is_internal(dev_node):
            self._core._request("playback.stop_playback")
            logger.debug(f"Unmounting {dev_node}...")
            try:
                self._proc_unmount = subprocess.run(
                    ["udisksctl", "unmount", "-b", dev_node],
                    text=True,
                    capture_output=True,
                )
                existing_device = self.on_info(dev_node)
                removed_device = None
                if not existing_device:
                    for key in ["mounted", "unmounted"]:
                        for device in self._storages[key]:
                            if device["dev"] == dev_node:
                                device["status"] = "removed"
                                removed_device = device
                                break

                response = removed_device or existing_device
                self._core.send(target="web", event="storage_updated", storage=response)
                logger.debug(self._proc_unmount.stdout.strip())
            except Exception as e:
                logger.error(f"Error unmounting {dev_node}: {e}")

    def monitor_usb(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem="block", device_type="partition")

        logger.info("Started monitoring USB devices...")
        for device in iter(monitor.poll, None):
            if device.action == "add":
                logger.info(f"Device added: {device.device_node}")
                self.mount_device(device.device_node)
                self._storages = get_storage_info()
            elif device.action == "remove":
                logger.info(f"Device removed: {device.device_node}")
                self.unmount_device(device.device_node)

    def mount_devices(self, dev_node: str | None = None):
        context = pyudev.Context()

        def is_mounted(node: str) -> bool:
            return any(p.device == node for p in psutil.disk_partitions(all=False))

        if dev_node:
            if is_mounted(dev_node):
                logger.debug(f"{dev_node} is already mounted.")
            else:
                self.mount_device(dev_node)
            return True

        for device in context.list_devices(subsystem="block", DEVTYPE="partition"):
            node = device.device_node
            if not is_mounted(node):
                self.mount_device(node)
