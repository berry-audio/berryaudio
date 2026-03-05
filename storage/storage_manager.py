import psutil
import pyudev
import subprocess
import re
import logging

from core.models import RefType, Storage
from pathlib import Path
from .smb_manager import StorageSMB

logger = logging.getLogger(__name__)

INTERNAL_MUSIC_DIR = "Internal"
INTERNAL_MUSIC_PATH = Path(f"/home/pi/{INTERNAL_MUSIC_DIR}")


class StorageManager:
    def __init__(self, name=None, core=None):
        self._core = core
        self._name = name

    def get_mounted_partitions(self) -> dict:
        mounts = {}
        for p in psutil.disk_partitions(all=False):
            if "rw" in p.opts and p.fstype:
                usage = psutil.disk_usage(p.mountpoint)
                mounts[p.device] = {
                    "mount": p.mountpoint,
                    "fstype": p.fstype,
                    "usage": usage,
                }
        return mounts

    def get_fs_info(self, dev: str) -> tuple[str, str]:
        try:
            output = subprocess.check_output(["blkid", dev], text=True).strip()
            fs_type = None
            label = None

            type_match = re.search(r'TYPE="([^"]+)"', output)
            if type_match:
                fs_type = type_match.group(1)

            label_match = re.search(r'LABEL="([^"]+)"', output)
            if label_match:
                label = label_match.group(1)

            return fs_type, label
        except subprocess.CalledProcessError:
            return None, None

    def _is_internal(self, dev_node: str) -> bool:
        if not Path(dev_node).exists():
            logger.warning(f"Device {dev_node} no longer exists")
            return False
          
        context = pyudev.Context()
        device = pyudev.Devices.from_device_file(context, dev_node)
        parent = device.find_parent("block")
        removable = bool(int(parent.attributes.get("removable", 0)))
        if not removable:
            logger.warning(f"Cannot mount/unmount internal storage: {dev_node}")
        return not removable

    def get_storage(self, dev: str) -> dict | None:
        for section in ("mounted", "unmounted"):
            data = self.get_storages_list()
            for item in data.get(section, []):
                if item.dev == dev:
                    return item
        return False

    def get_storages_list(self) -> dict[str, list[Storage]]:
        context = pyudev.Context()
        mounts = self.get_mounted_partitions()
        mounted = []
        unmounted = []

        INTERNAL_MUSIC_PATH.mkdir(parents=True, exist_ok=True)

        for device in context.list_devices(subsystem="block", DEVTYPE="partition"):
            devname = device.device_node
            is_internal = self._is_internal(devname)

            parent = device.find_parent("block").device_node
            size_bytes = int(device.attributes.asint("size")) * 512
            removable = bool(int(device.attributes.get("removable", 0)))
            fs_type, label = self.get_fs_info(devname)

            if devname in mounts:
                mount_point = mounts[devname]["mount"]

                if is_internal and mount_point == "/":
                    continue

                if is_internal:
                    mount_point = str(INTERNAL_MUSIC_PATH)

                u = mounts[devname]["usage"]
                storage = Storage(
                    dev=devname,
                    type=RefType.STORAGE,
                    parent=parent,
                    removable=removable,
                    size=size_bytes,
                    actual_size=int(size_bytes / 1_000_000_000),
                    fstype=fs_type,
                    name=INTERNAL_MUSIC_DIR if is_internal else label or "Unknown",
                    status="mounted",
                    uri=f"{self._name}:{mount_point}",
                    total=u.total,
                    used=u.used,
                    free=u.free,
                    percent=u.percent,
                )
                mounted.append(storage)
            else:
                if is_internal:
                    continue

                storage = Storage(
                    dev=devname,
                    type=RefType.STORAGE,
                    parent=parent,
                    removable=removable,
                    size=size_bytes,
                    actual_size=int(size_bytes / 1_000_000_000),
                    fstype=fs_type,
                    name=label or "Unknown",
                    status="unmounted",
                )
                unmounted.append(storage)

        self._storage_list = {"mounted": mounted, "unmounted": unmounted}

        return self._storage_list

    def list_directory(self, uri: str, extensions=None) -> list[Storage]:
        if not uri.startswith(f"{self._name}:"):
            raise ValueError(f"Not a valid storage path: {uri}")

        _, path = uri.split(":", 1)
        p = Path(path)

        _smb = StorageSMB()
        _smb_list_shares = {s.uri for s in _smb.list_shares()}

        entries = []
        try:
            for item in p.iterdir():
                if item.name.startswith("."):
                    continue

                item_uri = f"{self._name}:{str(item.resolve())}"

                if item.is_dir():
                    entries.append(
                        Storage(
                            name=item.name,
                            shared=item_uri in _smb_list_shares,
                            type=RefType.DIRECTORY,
                            size=0,
                            uri=item_uri,
                        )
                    )
                elif extensions is None or item.suffix.lower() in [
                    ext.lower() for ext in extensions
                ]:
                    entries.append(
                        Storage(
                            name=item.name,
                            shared=item_uri in _smb_list_shares,
                            type=RefType.TRACK,
                            size=item.stat().st_size,
                            uri=item_uri,
                        )
                    )

            entries.sort(key=lambda x: (x.type != RefType.DIRECTORY, x.name.lower()))
            return entries
        except Exception:
            return []

