import logging
import json

from pathlib import Path
from core.actor import Actor
from core.models import Image, RefType, Album, Artist, Ref, Track, Source
from core.types import PlaybackControls

logger = logging.getLogger(__name__)

STATIONS_PATH = Path(__file__).parent.parent / "radio" / "stations.json"
BASE_DIR = Path(__file__).resolve().parent.parent / "web" / "www"
ALBUM_IMAGES_WEB_PATH = Path("images") / "radio"


class RadioExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._source = Source(
            type=self._name,
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
        self._init_table()
        self._init_stations()
        logger.info("Started")

    async def on_stop(self):
        logger.info("Stopped")

    async def on_event(self, message):
        pass

    async def on_stop_service(self) -> bool:
        await self._core.request("playback.clear")
        return True

    async def on_start_service(self):
        logger.debug("Starting Service")
        return True

    def _init_table(self):
        self._db.executescript(
            """
            DROP TABLE IF EXISTS radio;

            CREATE TABLE radio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                name TEXT,
                genre TEXT,
                broadcaster TEXT,
                language TEXT,
                country TEXT,
                region TEXT,
                bitrate INTEGER,
                format TEXT,
                home_page TEXT,
                views INTEGER,
                image TEXT
            );
            """
        )

    def _init_stations(self):
        with open(STATIONS_PATH, "r", encoding="utf-8") as f:
            radios = json.load(f)

        self._db.executemany(
            """
            INSERT OR IGNORE INTO radio (
                path, name, genre, broadcaster, language,
                country, region, bitrate, format, home_page, image
            )
            VALUES (
                :path, :name, :genre, :broadcaster, :language,
                :country, :region, :bitrate, :format, :home_page, :image
            )
            """,
            radios,
        )

    def build_track(self, row, is_track: bool = True) -> any:
        obj = {
            "uri": f"radio:{row.id}",
            "name": row.name,
            "genre": row.genre or None,
        }

        if row.image:
            image_full_path = BASE_DIR / ALBUM_IMAGES_WEB_PATH / row.image
            image_path = ALBUM_IMAGES_WEB_PATH / row.image

            obj["images"] = (
                [Image(uri=str(image_path))] if image_full_path.is_file() else []
            )

        if is_track:
            obj["type"] = RefType.TRACK

        if row.country:
            obj["albums"] = frozenset([Album(name=row.country)])

        if row.broadcaster:
            obj["artists"] = frozenset([Artist(name=f"{row.genre} / {row.country}")])
        return obj

    def on_directory(
        self,
        uri: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        if not uri:
            raise ValueError(f"No 'uri' was defined.")

        values = uri.split(":")
        values_len = len(values)

        if values_len and values_len == 1:
            base_sql = (
                f"""
                    SELECT 
                        a.*
                    FROM radio a
                    WHERE %s
                    ORDER BY a.name ASC
                """
                % "1"
            )
            sql = base_sql.rstrip(";")

            params = []
            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)

                if offset is not None:
                    sql += " OFFSET ?"
                    params.append(offset)

            rows = self._db.fetchall(sql, params)
        return [Ref(**self.build_track(row)) for row in rows]

    async def on_playback_uri(self, id: int) -> any:
        self._core._request("source.update_source", source=self._source)
        row = self._db.fetchone(f"SELECT * FROM radio WHERE id = {id}")
        return row.path if row else None

    async def on_lookup_track(self, id: int) -> Track:
        row = self._db.fetchall(f"SELECT * FROM radio WHERE id = {id}")
        return Track(**self.build_track(row[0], False))
