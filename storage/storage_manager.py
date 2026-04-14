import psutil
import pydbus
import asyncio
import logging

from pathlib import Path
from gi.repository import GLib
from core.models import RefType, Storage, StorageUsage
from core.util.system import SystemUtil

from .smb_manager import StorageSmbManager

logger = logging.getLogger(__name__)

INTERNAL_MUSIC_DIR = "Internal"
INTERNAL_MUSIC_PATH = Path(f"/home/pi/{INTERNAL_MUSIC_DIR}")


class StorageManager:
    def __init__(self, name=None, core=None, db=None):
        self._core = core
        self._name = name
        self.db = db
        self._system = SystemUtil(self._core, self.db)
        self._bus = pydbus.SystemBus()
        self._udisks = self._bus.get(
            "org.freedesktop.UDisks2", "/org/freedesktop/UDisks2"
        )
        self._smb = StorageSmbManager(
            name=self._name, core=self._core, username=None, password=None
        )
        self._storage_list = []

    def storage_item(
        self, dev: str, internal: bool = False
    ) -> dict | None:  ##todo use uri\
        if internal:
            storage_list = self.storages_internal()
        else:
            storage_list = self.storages_list()
        for item in storage_list:
            if item.dev == dev:
                return item
        return False

    def storages_internal(self) -> list[Storage]:
        objects = self._udisks.GetManagedObjects()
        storages = []
        INTERNAL_MUSIC_PATH.mkdir(parents=True, exist_ok=True)

        def decode_bytes(b_array):
            return "".join(chr(b) for b in b_array if b != 0)

        for path, interfaces in objects.items():
            if "org.freedesktop.UDisks2.Block" not in interfaces:
                continue

            block = interfaces["org.freedesktop.UDisks2.Block"]
            if "org.freedesktop.UDisks2.Filesystem" not in interfaces:
                continue

            try:
                devname = decode_bytes(block.get("PreferredDevice", []))
                fs_type = block.get("IdType", "") or "Unknown"
                label = block.get("IdLabel", "") or None

                drive_path = block.get("Drive")
                if drive_path and drive_path != "/":
                    drive = self._bus.get("org.freedesktop.UDisks2", drive_path)
                    connection_bus = drive.ConnectionBus
                else:
                    connection_bus = ""

                is_internal = connection_bus in ("sdio", "ata", "nvme", "")

                fs = interfaces.get("org.freedesktop.UDisks2.Filesystem", {})
                mount_points = fs.get("MountPoints", [])
                mountpoint = decode_bytes(mount_points[0]) if mount_points else None

                if mountpoint:
                    if is_internal and mountpoint == "/":
                        continue

                    if is_internal:
                        mountpoint = str(INTERNAL_MUSIC_PATH)

                    try:
                        u = psutil.disk_usage(mountpoint)
                        usage = StorageUsage(
                            total=u.total,
                            used=u.used,
                            free=u.free,
                        )
                    except Exception:
                        usage = None

                    storages.append(
                        Storage(
                            type=RefType.STORAGE if is_internal else RefType.REMOVABLE,
                            name=(
                                INTERNAL_MUSIC_DIR
                                if is_internal
                                else label or "Unknown"
                            ),
                            dev=devname,
                            fstype=fs_type,
                            status="mounted",
                            uri=f"{self._name}:{mountpoint}",
                            usage=usage,
                        )
                    )

                else:
                    if is_internal:
                        continue

                    storages.append(
                        Storage(
                            type=RefType.REMOVABLE,
                            name=label or "Unknown",
                            dev=devname,
                            fstype=fs_type,
                            status="unmounted",
                        )
                    )

            except Exception as e:
                print(f"Error reading {path}: {e}")
                continue
        return storages

    def storages_list(self) -> list[Storage]:
        storages = self.storages_internal()
        storages.extend(self._smb.list_smb_shared())
        return storages

    async def storage_mount(self, dev_node: str) -> str | None:
        device = dev_node.replace("/dev/", "")
        logger.debug(f"Mounting {dev_node}")

        loop = asyncio.get_event_loop()

        try:
            obj = self._bus.get(
                "org.freedesktop.UDisks2",
                f"/org/freedesktop/UDisks2/block_devices/{device}",
            )

            existing = await loop.run_in_executor(None, lambda: obj.MountPoints)
            if existing:
                mount_point = "".join(chr(b) for b in existing[0] if b != 0)
                raise ValueError(f"{dev_node} already mounted at {mount_point}")

            # Stop camilladsp before mounting to prevent cpu throttling on pizero 2W
            if self._system.get_board() == "PI_ZERO_2W":
                await self._core.request("dsp.service", state="stop")
            mount_point = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: obj.Mount(
                        {"auth.no_user_interaction": GLib.Variant("b", True)}
                    ),
                ),
                timeout=60,
            )

            logger.debug(f"Mounted {dev_node} at {mount_point}")
            storage = await loop.run_in_executor(
                None, lambda: self.storage_item(dev_node, internal=True)
            )

            if self._system.get_board() == "PI_ZERO_2W":
                await self._core.request("dsp.service", state="start")

            logger.info(
                f"Mounted {dev_node}, Total: {storage.usage.total}, "
                f"Used: {storage.usage.used}, Free: {storage.usage.free}"
            )

            if mount_point:
                self._core.send(
                    target=["web", "display"], event="storage_mounted", storage=storage
                )
                return True

        except asyncio.TimeoutError:
            raise ValueError(f"Mount timed out for {dev_node}")
        except Exception as e:
            raise ValueError(f"Error mounting {dev_node}: {e}")

    async def storage_unmount(self, dev_node: str) -> bool:
        device = dev_node.replace("/dev/", "")
        logger.debug(f"Unmounting {dev_node}")

        try:
            obj = self._bus.get(
                "org.freedesktop.UDisks2",
                f"/org/freedesktop/UDisks2/block_devices/{device}",
            )

            existing = obj.MountPoints
            if not existing:
                logger.debug(f"{dev_node} is not mounted, skipping unmount")
            else:
                obj.Unmount({"auth.no_user_interaction": GLib.Variant("b", True)})
                logger.debug(f"Unmounted {dev_node}")

            self._core._request("playback.stop")
            storage = self.storage_item(dev_node, internal=True)

            if not storage:
                self._core.send(
                    target=["web", "display"],
                    event="storage_removed",
                    storage=storage,
                )
                return True

            self._core.send(
                target=["web", "display"],
                event="storage_unmounted",
                storage=storage,
            )
            return True

        except Exception as e:
            raise ValueError(f"Error unmounting {dev_node}: {e}")

    def directory(
        self,
        uri: str,
        extensions=None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict:
        if not uri.startswith(f"{self._name}:"):
            raise ValueError(f"Not a valid storage path: {uri}")

        _, path = uri.split(":", 1)
        p = Path(path)
        _smb_list_shares = {s.uri for s in self._smb.list_shares()}
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

            _offset = offset or 0
            paginated = entries[_offset:]
            if limit is not None:
                paginated = paginated[:limit]

            return paginated

        except Exception:
            return []
