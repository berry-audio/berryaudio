import logging
import pyudev
import threading
import psutil
import subprocess
import asyncio

from core.actor import SourceActor
from core.types import PlaybackControls
from core.util.metadata import Metadata
from core.models import Image, Album, Artist, Track, Source, RefType

from pathlib import Path
from .smb_manager import StorageSMB
from .storage_manager import StorageManager

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent / "web" / "www"


class StorageExtension(SourceActor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._album_images_full_path = BASE_DIR / "images" / self._name
        self._album_images_web_path = Path("images") / self._name
        self._metadata = Metadata(cover_dir=self._album_images_full_path)
        self._smb = StorageSMB(
            name=self._name,
            core=self._core,
            db=self._db,
            username=self._config[self._name]["username"],
            password=self._config[self._name]["password"],
        )
        self._storage = StorageManager(name=self._name, core=self._core)
        self._storage_list = self._storage.get_storages_list()
        self._loop = asyncio.get_event_loop()
        self._source = Source(
            name="Storage",
            type=RefType.SOURCE,
            uri=self._name,
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
        config_smb_clients = self._config.get(self._name, {}).get("smb_clients", {})
        if config_smb_clients:
            for dev, creds in config_smb_clients.items():
                try:
                    await self._smb.mount_shared(
                        devs=[dev],
                        username=creds.get("username"),
                        password=creds.get("password", ""),
                    )
                except (
                    ValueError,
                    PermissionError,
                    ConnectionError,
                    FileNotFoundError,
                ) as e:
                    logger.error(e)
        threading.Thread(target=self._monitor_usb, daemon=True).start()
        await self._smb.status()
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

    async def on_start_service(self):
        return True

    async def on_stop_service(self):
        await self._core.request("playback.clear")
        return True

    def _build_ref(self, uri: str) -> dict:
        cover_path, tags = self._metadata.extract_cover_and_tags(uri)  # id is full path
        image_uri = None

        if cover_path:
            image_full_path = Path(self._album_images_full_path) / cover_path
            image_web_path = Path(self._album_images_web_path) / cover_path

            if image_full_path.is_file():
                image_uri = str(image_web_path)

        obj: dict = {
            "uri": f"{self._name}:{uri}",
            "images": [Image(uri=image_uri)] if image_uri else [],
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

    async def on_playback_uri(self, path: str) -> any:
        self._core._request("source.update_source", source=self._source)
        path = Path(path).as_uri()
        return f"{path}" if id else None

    async def on_lookup_track(self, path: str) -> Track:
        return Track(**self._build_ref(path))

    async def on_directory(
        self, uri: str = None, limit: int | None = None, offset: int | None = None
    ):
        if uri is None:
            return self._storage.get_storages_list()
        else:
            return self._storage.list_directory(
                uri,
                extensions=[
                    ".mp3",
                    ".m4a",
                    ".flac",
                    ".wav",
                    ".ogg",
                    ".aac",
                    ".dsf",
                    ".dsf",
                ],
                limit=limit,
                offset=offset,
            )

    def _handle_library_paths(self, uri: str, *, add: bool) -> bool:
        if not uri.startswith(f"{self._name}:"):
            raise ValueError(f"Not a valid {self._name} path: {uri}")

        library_paths = self._config.get("local", {}).get("library_path", [])

        if add and uri not in library_paths:
            library_paths.append(uri)
        elif not add and uri in library_paths:
            library_paths.remove(uri)
        else:
            return False

        self._db.set_config({"local": {"library_path": library_paths}})
        return True

    def on_add_to_library(self, uri: str) -> bool:
        return self._handle_library_paths(uri, add=True)

    def on_remove_from_library(self, uri: str) -> bool:
        return self._handle_library_paths(uri, add=False)

    def on_mount(self, dev: str):
        return self._mount_device(dev)

    def on_unmount(self, dev: str):
        return self._unmount_device(dev)

    def on_add_shared(self, ip: str, username: str = None, password: str = None):
        return self._smb.add_shared(ip, username, password)

    async def on_mount_shared(self, devs: list[str]):
        return await self._smb.mount_shared(devs)

    async def on_unmount_shared(self, dev: str):
        return await self._smb.unmount_shared(dev)

    def on_list_smb_shared(self):
        return self._smb.list_smb_shared()

    def on_list_shares(self):
        return self._smb.list_shares()

    async def on_unshare(self, uri: str):
        return await self._smb.unshare(uri)

    async def on_share(self, uri: str, name: str = None, read_only: bool = False):
        return await self._smb.share(uri, name, read_only)

    def _monitor_usb(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem="block", device_type="partition")
        logger.info("Started monitoring USB devices")

        for device in iter(monitor.poll, None):
            if device.action == "add":
                self.mount_device(device.device_node)
                self._storage_list = self._storage.get_storages_list()
                logger.info(f"Device mounted: {device.device_node}")

            elif device.action == "remove":
                self.unmount_device(device.device_node)
                logger.info(f"Device removed: {device.device_node}")

    def _mount_device(self, dev_node: str) -> str | None:
        if self._storage._is_internal(dev_node):
            raise ValueError(f"Cannot mount internal device {dev_node}")

        logger.debug(f"Mounting {dev_node}")
        try:
            result = subprocess.run(
                ["udisksctl", "mount", "-b", dev_node],
                text=True,
                capture_output=True,
            )
            logger.debug(result.stdout.strip())

            mount_point = None
            for line in result.stdout.splitlines():
                if "Mounted" in line:
                    mount_point = line.split(" at ")[1].rstrip(".")
                    break

            if mount_point:
                usage = psutil.disk_usage(mount_point)
                self._core.send(
                    target=["web", "display"],
                    event="storage_mounted",
                    storage=self._storage.get_storage(dev_node),
                )
                logger.info(
                    f"Mounted {mount_point}, Total: {usage.total}, "
                    f"Used: {usage.used}, Free: {usage.free}"
                )

            return mount_point

        except Exception as e:
            raise ValueError(f"Error mounting {dev_node}: {e}")

    def mount_devices(self, dev: str | None = None) -> bool:
        context = pyudev.Context()

        def _is_mounted(node: str) -> bool:
            return any(p.device == node for p in psutil.disk_partitions(all=False))

        if dev:
            if _is_mounted(dev):
                logger.debug(f"{dev} is already mounted.")
                return False
            self.mount_device(dev)
            return True

        for device in context.list_devices(subsystem="block", DEVTYPE="partition"):
            node = device.device_node
            if not _is_mounted(node):
                self.mount_device(node)
        return True

    def _unmount_device(self, dev: str) -> bool:
        if self._storage._is_internal(dev):
            raise ValueError(f"Cannot unmount internal device {dev}")

        logger.debug(f"Unmounting {dev}")

        try:
            result = subprocess.run(
                ["udisksctl", "unmount", "-b", dev],
                text=True,
                capture_output=True,
            )
            logger.debug(result.stdout.strip())

            self._core._request("playback.stop_playback")
            _storage = self._storage.get_storage(dev)

            if not _storage:
                for device in self._storage_list:
                    if device.dev == dev:
                        self._core.send(
                            target=["web", "display"],
                            event="storage_removed",
                            storage=device,
                        )
                        break

            if not _storage:
                return True

            self._core.send(
                target=["web", "display"],
                event="storage_unmounted",
                storage=_storage,
            )
            return True

        except Exception as e:
            raise ValueError(f"Error unmounting {dev}: {e}")
