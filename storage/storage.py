import logging
import pyudev
import subprocess
import asyncio

from core.actor import SourceActor
from core.types import PlaybackControls
from core.util.metadata import Metadata
from core.models import Image, Album, Artist, Track, Source, RefType

from pathlib import Path
from .smb_manager import StorageSmbManager
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
        self._smb = StorageSmbManager(
            name=self._name,
            core=self._core,
            db=self._db,
            username=self._config[self._name]["username"],
            password=self._config[self._name]["password"],
        )
        self._storage = StorageManager(name=self._name, core=self._core, db=self._db)
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
        # threading.Thread(target=self._monitor_usb, daemon=True).start()
        await self._smb.status()
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

    async def on_start_service(self):
        logger.debug("Starting Service")
        return self._source

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
        path = Path(path).as_uri()
        return f"{path}" if id else None

    async def on_lookup_track(self, path: str) -> Track:
        return Track(**self._build_ref(path))

    async def on_directory(
        self, uri: str = None, limit: int | None = None, offset: int | None = None
    ):
        if uri is None:
            return self._storage.storages_list()
        else:
            return self._storage.directory(
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

        if add:
            if uri in library_paths:
                raise ValueError("Path already exists in library")
            library_paths.append(uri)
        else:
            if uri not in library_paths:
                raise ValueError("Path does not exist in library")
            library_paths.remove(uri)

        self._db.set_config({"local": {"library_path": library_paths}})
        return True

    def on_add_to_library(self, uri: str) -> bool:
        return self._handle_library_paths(uri, add=True)

    def on_remove_from_library(self, uri: str) -> bool:
        return self._handle_library_paths(uri, add=False)

    async def on_mount(self, dev: str):
        return await self._storage.storage_mount(dev)

    async def on_unmount(self, dev: str):
        return await self._storage.storage_unmount(dev)

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
