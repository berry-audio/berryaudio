import logging
import asyncio
import requests
import os
import re

from urllib.parse import quote
from core.actor import Actor
from core.types import PlaybackControls
from core.util.metadata import Metadata
from core.models import Image, RefType, Album, Artist, Ref, Track, Source
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

AUDIO_EXTS = {
    ".mp3",
    ".m4a",
    ".mp4",
    ".aac",
    ".flac",
    ".ogg",
    ".opus",
    ".wma",
    ".wav",
    ".dsf",
}
BASE_DIR = Path(__file__).parent.parent / "web" / "www"

ALBUM_IMAGES_DIR = BASE_DIR / "images" / "album"
ALBUM_IMAGES_WEB_PATH = Path("images") / "album"

ARTIST_IMAGES_DIR = BASE_DIR / "images" / "artist"
ARTIST_IMAGES_WEB_PATH = Path("images") / "artist"

AUDIO_DB_API = "https://www.theaudiodb.com/api/v1/json/123/search.php?s={artist}"
BATCH_SIZE = 50

SCHEMA_SQL = """
    PRAGMA journal_mode=WAL;
    PRAGMA foreign_keys=ON;

    CREATE TABLE IF NOT EXISTS artist (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE COLLATE NOCASE,
        image TEXT,
        comment TEXT,
        country TEXT,
        genre TEXT,
        musicbrainz_id TEXT
    );

    CREATE TABLE IF NOT EXISTS genre (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE COLLATE NOCASE
    );

    CREATE TABLE IF NOT EXISTS album (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL COLLATE NOCASE,
        artist_id INTEGER,
        year INTEGER,
        image TEXT,
        musicbrainz_id TEXT,
        UNIQUE(name, artist_id),
        FOREIGN KEY (artist_id) REFERENCES artist(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS track (
        id INTEGER PRIMARY KEY,
        file_path TEXT NOT NULL UNIQUE,
        file_name TEXT NOT NULL,
        name TEXT,
        track_number INTEGER,
        disc_number INTEGER,
        length REAL,
        bitrate INTEGER,
        sample_rate INTEGER,
        album_id INTEGER,
        artist_id INTEGER,
        genre_id INTEGER,
        musicbrainz_id TEXT,
        image TEXT,
        mtime REAL,
        added_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (album_id) REFERENCES album(id) ON DELETE SET NULL,
        FOREIGN KEY (artist_id) REFERENCES artist(id) ON DELETE SET NULL,
        FOREIGN KEY (genre_id) REFERENCES genre(id) ON DELETE SET NULL
    );
    """
QUERIES = {
    "track": f"""
            SELECT
                a.*,
                ab.id AS album_id,
                ab.name AS album_name,
                ab.year AS album_year,
                ab.image AS album_image,
                ar.id AS artist_id,
                ar.name AS artist_name,
                ar.image AS artist_image,
                g.id AS genre_id,
                g.name AS genre_name
            FROM track a
            LEFT JOIN album ab ON a.album_id = ab.id
            LEFT JOIN artist ar ON a.artist_id = ar.id
            LEFT JOIN genre g ON a.genre_id = g.id
            WHERE %s
            ORDER BY a.name ASC
        """,
    "album": f"""
            SELECT 
                a.id AS id,
                a.name,
                a.image as image,
                a.year as year,
                a.artist_id,
                ar.name AS artist_name,
                ar.image AS artist_image,
                COUNT(t.id) AS length
            FROM album a
            LEFT JOIN artist ar ON a.artist_id = ar.id
            LEFT JOIN track t ON t.album_id = a.id
            WHERE %s
            GROUP BY a.id, ar.name
            ORDER BY a.name ASC
        """,
    "artist": f"""
            SELECT 
                a.*,
                (SELECT COUNT(*) FROM track t WHERE t.artist_id = a.id) AS length
            FROM artist a
            WHERE %s
            ORDER BY a.name ASC
            
        """,
    "genre": f"""
            SELECT 
                a.*,
                (SELECT COUNT(*) FROM track t WHERE t.genre_id = a.id) AS length
            FROM genre a
            WHERE %s
            ORDER BY a.name ASC
        """,
    "radio": f"""
            SELECT 
                a.*
            FROM radio a
            WHERE %s
            ORDER BY a.name ASC
        """,
}

TYPES = {
    "track": RefType.TRACK,
    "album": RefType.ALBUM,
    "artist": RefType.ARTIST,
    "genre": RefType.DIRECTORY,
}


class LocalExtension(Actor):
    default_config = {
        "library_path": [],
    }

    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._metadata = Metadata(cover_dir="albums")
        self._scan_progress = None
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
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

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

        if values_len:
            if values_len == 3:
                view, ref_id, ref_type = values

                if view == RefType.TRACK:
                    raise ValueError(f"Track does not have listings")

                if ref_type != "list":
                    raise ValueError(f"View type '{ref_type}' not supported")

                sql = QUERIES["track"] % (f"a.{view}_id = {ref_id}")
                rows = self._db.fetchall(sql)
                view = "track"

            if values_len == 2:
                view, ref_id = values

                sql = QUERIES[view] % "a.id = ?"
                rows = self._db.fetchall(sql, (ref_id,))

            if values_len == 1:
                view = values[0]
                base_sql = QUERIES[view] % "1"
                sql = base_sql.rstrip(";")

                params = []
                if limit is not None:
                    sql += " LIMIT ?"
                    params.append(limit)

                    if offset is not None:
                        sql += " OFFSET ?"
                        params.append(offset)
                rows = self._db.fetchall(sql, params)
            return [Ref(**self._build_ref(row, view)) for row in rows]

    def _build_ref(self, row, view, is_ref=True):
        obj = {}
        obj["uri"] = f"{'local' if view == 'track' else view}:{row.id}"

        if is_ref:
            obj["type"] = TYPES[view]

        if row.name:
            obj["name"] = row.name

        if row.album_name:
            image_uri = None

            if row.album_image:
                image_full_path = ALBUM_IMAGES_DIR / row.album_image
                image_web_path = ALBUM_IMAGES_WEB_PATH / row.album_image

                if image_full_path.is_file():
                    image_uri = str(image_web_path)

            obj["albums"] = frozenset(
                [
                    Album(
                        uri=f"album:{row.album_id}",
                        name=row.album_name,
                        date=row.album_year or None,
                        images=[Image(uri=image_uri)] if image_uri else [],
                    )
                ]
            )

        if row.artist_name:
            image_uri = None

            if row.artist_image:
                image_full_path = ARTIST_IMAGES_DIR / row.artist_image
                image_web_path = ARTIST_IMAGES_WEB_PATH / row.artist_image

                if image_full_path.is_file():
                    image_uri = str(image_web_path)

            obj["artists"] = frozenset(
                [
                    Artist(
                        uri=f"artist:{row.artist_id}",
                        name=row.artist_name,
                        images=[Image(uri=image_uri)] if image_uri else [],
                    )
                ]
            )
        if row.genre:
            obj["genre"] = row.genre

        if row.genre_name:
            obj["genre"] = row.genre_name

        if row.country:
            obj["country"] = row.country

        if row.year:
            obj["date"] = row.year

        if row.track_number:
            obj["track_no"] = row.track_number

        if row.disc_number:
            obj["disc_no"] = row.track_number

        if row.bitrate:
            obj["bitrate"] = row.bitrate

        if row.length:
            obj["length"] = int(row.length)

        if row.comment:
            obj["comment"] = row.comment

        image_uri = None
        if row.image:
            image_full_path = (
                ARTIST_IMAGES_DIR if view == "artist" else ALBUM_IMAGES_DIR
            ) / row.image

            image_web_path = (
                ARTIST_IMAGES_WEB_PATH if view == "artist" else ALBUM_IMAGES_WEB_PATH
            ) / row.image

            if image_full_path.is_file():
                image_uri = str(image_web_path)

        obj["images"] = [Image(uri=image_uri)] if image_uri else []

        return obj

    async def on_playback_uri(self, id: int) -> any:
        self._core._request("source.update_source", source=self._source)
        row = self._db.fetchone(f"SELECT * FROM track WHERE id = {id}")
        return f"file://{row.file_path}" if row else None

    async def on_lookup_track(self, id: int) -> Track:
        sql = QUERIES["track"] % (f"a.id = {id}")
        row = self._db.fetchall(sql)
        return Track(**self._build_ref(row[0], "track", False))

    async def on_stop_service(self) -> bool:
        await self._core.request("playback.clear")
        return True

    async def on_start_service(self) -> bool:
        logger.debug("Starting Service")
        return True

    async def on_clean(self):
        self._db.executescript(
            """
            DROP TABLE IF EXISTS artist;
            DROP TABLE IF EXISTS album;
            DROP TABLE IF EXISTS genre;
            DROP TABLE IF EXISTS track;
        """
        )
        logger.info("Cleared library")

        for file_path in Path(ALBUM_IMAGES_DIR).iterdir():
            if file_path.name != ".gitkeep" and file_path.is_file():
                try:
                    file_path.unlink()
                    logger.debug(f"Deleted {file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete {file_path}: {e}")

        logger.info("Cleared images in %s", ALBUM_IMAGES_DIR)
        return True

    def on_scan_progress(self):
        return self._scan_progress

    def on_scan(self):
        asyncio.create_task(self.scan_and_ingest())
        return True

    def on_scan_artists(self):
        asyncio.create_task(self.scan_and_download_artist_info())
        return True

    # -- Download Artist Info ---
    def normalize_artist_name(self, raw_name):
        """If multiple artists, take only the first one."""
        parts = re.split(
            r"\s*(?:&|,|;|feat\.|ft\.|with|/)\s*", raw_name, flags=re.IGNORECASE
        )
        return parts[0].strip()

    def fetch_artist_info(self, artist_name):
        """Fetch artist image URL from TheAudioDB API."""
        try:
            url = AUDIO_DB_API.format(artist=artist_name)
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data and data.get("artists"):
                artist = data["artists"][0]
                return {
                    "thumb": artist.get("strArtistThumb"),
                    "biography": artist.get("strBiographyEN"),
                    "genre": artist.get("strGenre"),
                    "country": artist.get("strCountry"),
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching {artist_name}: {e}")

    def download_artist_image(self, url, filename):
        """Download and save image from URL."""
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            with open(filename, "wb") as f:
                f.write(resp.content)
            return True
        except Exception as e:
            logger.error(f"Error downloading image {url}: {e}")
            return False

    async def scan_and_download_artist_info(self):
        sql = QUERIES["artist"] % "1"
        artists = self._db.fetchall(sql)
        _scan_artist_progress = {
            "updated": 0,
            "downloaded": 0,
            "unavailable": 0,
            "completed": False,
        }

        self._core.send(
            target="web",
            event="scan_artist_updated",
            progress=_scan_artist_progress.copy(),
        )
        await asyncio.sleep(0.2)

        for artist in artists:
            filename = ARTIST_IMAGES_DIR / f"{artist.name}.jpg"
            filename_db = f"{artist.name}.jpg"

            if artist.image and (Path(ARTIST_IMAGES_DIR) / artist.image).exists():
                logger.debug(f"Skipping {artist.name}, already has image.")
                continue

            # pass 1
            result = self.fetch_artist_info(quote(artist.name))

            if not result:
                # pass 2
                result = self.fetch_artist_info(self.normalize_artist_name(artist.name))
                if not result:
                    logger.warning(f"No data found for {artist.name}")
                    _scan_artist_progress["unavailable"] += 1
                    continue

            if Path(filename).exists():
                logger.debug(f"File already exists for {artist.name}, updating DB...")
                self._db.execute(
                    "UPDATE artist SET image = ?, comment = ?, genre = ?, country = ?  WHERE id = ?",
                    (
                        filename_db,
                        result["biography"],
                        result["genre"],
                        result["country"],
                        artist.id,
                    ),
                )
                _scan_artist_progress["updated"] += 1
                continue

            if self.download_artist_image(result["thumb"], filename):
                logger.debug(f"Saved {artist.name} image to {filename}")
                self._db.execute(
                    "UPDATE artist SET image = ?, comment = ? , genre = ?, country = ? WHERE id = ?",
                    (
                        filename_db,
                        result["biography"],
                        result["genre"],
                        result["country"],
                        artist.id,
                    ),
                )
                _scan_artist_progress["updated"] += 1
                _scan_artist_progress["downloaded"] += 1
                await asyncio.sleep(0.2)

            self._core.send(
                target="web",
                event="scan_artist_updated",
                progress=_scan_artist_progress.copy(),
            )
            await asyncio.sleep(0.2)

        _scan_artist_progress["completed"] = True
        self._core.send(
            target="web",
            event="scan_artist_updated",
            progress=_scan_artist_progress.copy(),
        )

    # ----- Scan Music --------

    def normalize_name(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return value.strip() or None

    def get_or_create(
        self, table: str, field: str, value: Optional[str]
    ) -> Optional[int]:
        """
        Insert if not exists, ignoring case for uniqueness.
        """
        value = self.normalize_name(value)
        if not value:
            return None

        row = self._db.fetchone(
            f"SELECT id FROM {table} WHERE {field} = ? COLLATE NOCASE", (value,)
        )
        if row:
            return row.id  # thanks to AttrRow

        cur = self._db.execute(f"INSERT INTO {table} ({field}) VALUES (?)", (value,))
        return cur.lastrowid

    def get_or_create_album(
        self,
        name: Optional[str],
        artist_id: Optional[int],
        year: Optional[int],
        image: Optional[str] = None,
    ) -> Optional[int]:
        name = self.normalize_name(name)
        if not name:
            return None

        row = self._db.fetchone(
            "SELECT id, image FROM album WHERE name = ? COLLATE NOCASE "
            "AND (artist_id IS ? OR artist_id = ?)",
            (name, artist_id, artist_id),
        )

        if row:
            # If no image is stored yet, update with new one
            if image and not row.image:
                self._db.execute("UPDATE album SET image=? WHERE id=?", (image, row.id))
            return row.id

        cur = self._db.execute(
            "INSERT INTO album (name, artist_id, year, image) VALUES (?, ?, ?, ?)",
            (name, artist_id, year, image),
        )
        return cur.lastrowid

    def is_audio(self, filename: str) -> bool:
        return os.path.splitext(filename)[1].lower() in AUDIO_EXTS

    async def scan_and_ingest(self):
        self._db.executescript(SCHEMA_SQL)
        _config = self._db.get_config()
        _scan_paths = _config["local"]["library_path"]

        self._scan_progress = {
            "processed": 0,
            "inserted": 0,
            "updated": 0,
            "completed": False,
        }
        self._core.send(
            target="web", event="scan_update", progress=self._scan_progress.copy()
        )
        await asyncio.sleep(0.3)
        logger.info(self._scan_progress)

        for root in _scan_paths:
            if not os.path.isdir(root):
                logger.warning(f"Skip non-existent path: {root}")
                continue

            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    if fn.startswith("."):
                        continue

                    if not self.is_audio(fn):
                        continue

                    fullpath = os.path.join(dirpath, fn)
                    try:
                        mtime = os.path.getmtime(fullpath)

                        # Check if already in DB with same mtime
                        row = self._db.fetchone(
                            "SELECT id, mtime FROM track WHERE file_path = ?",
                            (fullpath,),
                        )
                        if (
                            row
                            and row.mtime
                            and abs(float(row.mtime) - float(mtime)) < 0.0001
                        ):
                            logger.debug(f"Skipping unchanged: {fullpath}")
                            continue

                        cover_path, tags = self._metadata.extract_cover_and_tags(
                            fullpath
                        )

                        artist_id = self.get_or_create("artist", "name", tags["artist"])
                        genre_id = self.get_or_create("genre", "name", tags["genre"])
                        album_id = self.get_or_create_album(
                            tags["album"], artist_id, tags["year"], cover_path
                        )

                        file_name = os.path.basename(fullpath)
                        logger.debug(f"Processing file:{fullpath}")

                        if not tags["length"]:
                            continue

                        if row:
                            self._db.execute(
                                """UPDATE track SET
                                    file_name=?, name=?, track_number=?, disc_number=?, length=?, bitrate=?, sample_rate=?,
                                    album_id=?, artist_id=?, genre_id=?, image=?, mtime=?
                                WHERE id=?""",
                                (
                                    file_name,
                                    tags["name"],
                                    tags["track_number"],
                                    tags["disc_number"],
                                    tags["length"],
                                    tags["bitrate"],
                                    tags["sample_rate"],
                                    album_id,
                                    artist_id,
                                    genre_id,
                                    cover_path,
                                    mtime,
                                    row.id,
                                ),
                            )
                            self._scan_progress["updated"] += 1
                        else:
                            self._db.execute(
                                """INSERT INTO track
                                    (file_path, file_name, name, track_number, disc_number, length, bitrate, sample_rate,
                                    album_id, artist_id, genre_id, image, mtime)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                (
                                    fullpath,
                                    file_name,
                                    tags["name"],
                                    tags["track_number"],
                                    tags["disc_number"],
                                    tags["length"],
                                    tags["bitrate"],
                                    tags["sample_rate"],
                                    album_id,
                                    artist_id,
                                    genre_id,
                                    cover_path,
                                    mtime,
                                ),
                            )
                            self._scan_progress["inserted"] += 1
                        self._scan_progress["processed"] += 1
                        if self._scan_progress["processed"] % BATCH_SIZE == 0:
                            self._core.send(
                                target="web",
                                event="scan_update",
                                progress=self._scan_progress.copy(),
                            )
                            await asyncio.sleep(0.3)
                            logger.info(self._scan_progress)

                    except Exception as e:
                        logger.error(f"Error processing {fullpath}: {e}", exc_info=True)

        self._scan_progress["completed"] = True
        self._core.send(
            target="web", event="scan_update", progress=self._scan_progress.copy()
        )
        logger.info(self._scan_progress)
