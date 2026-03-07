import logging

from pathlib import Path
from typing import Dict, List
from core.actor import Actor
from core.models import Image, RefType, Album, Artist, Ref
from local.local import QUERIES

logger = logging.getLogger(__name__)
tables_to_search = ["artist", "album", "genre", "track", "radio"]

BASE_DIR = Path(__file__).parent.parent / "web" / "www" / "images"
IMAGES_WEB_PATH = Path("images") 

TYPES = {
    "track": RefType.TRACK,
    "album": RefType.ALBUM,
    "artist": RefType.ARTIST,
    "genre": RefType.DIRECTORY,
    "radio": RefType.TRACK,
}


class SearchExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config

    async def on_start(self):
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

    def search_tables(self, term: str, tables: List[str]) -> Dict[str, List[dict]]:
        results: Dict[str, List[dict]] = {}

        for table_name in tables:
            base_sql = QUERIES.get(table_name)
            if not base_sql:
                continue
            try:
                sql = base_sql % "a.name LIKE ? COLLATE NOCASE"
                rows = self._db.fetchall(sql, (f"%{term}%",))
                if rows:
                    results[table_name] = rows
            except Exception as e:
                print(f"Error with {table_name}: {e}")
                continue

        return results

    def on_search(self, query):
        matches = self.search_tables(query, tables_to_search)
        if not matches:
            return {}

        result = {
            table: [Ref(**self._build_ref(row, table)) for row in rows]
            for table, rows in matches.items()
        }
        return result

    def _build_ref(self, row, table, is_ref=True):
        obj = {}

        uri = "local" if table == "track" else table
        obj["uri"] = f"{uri}:{row.id}"

        if is_ref:
            obj["type"] = TYPES[table]

        if row.name:
            obj["name"] = row.name

        if row.album_name:
            obj["albums"] = frozenset(
                [
                    Album(
                        uri=f"album:{row.album_id}",
                        name=row.album_name,
                        date=row.album_year or None,
                        images=[Image(uri=row.album_image)] if row.album_image else [],
                    )
                ]
            )

        if row.artist_name:
            obj["artists"] = frozenset(
                [
                    Artist(
                        uri=f"artist:{row.artist_id}",
                        name=row.artist_name,
                        images=(
                            [Image(uri=row.artist_image)] if row.artist_image else []
                        ),
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
            directory = "album" if table == "track" else table
            image_full_path = BASE_DIR / directory / row.image
            image_web_path = IMAGES_WEB_PATH / directory / row.image

            if image_full_path.is_file():
                image_uri = str(image_web_path)

        obj["images"] = [Image(uri=image_uri)] if image_uri else []

        return obj
