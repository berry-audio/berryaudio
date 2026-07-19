import logging
import json

from pathlib import Path
from core.actor import SourceActor
from core.models import Image, Album, Artist, Track, Source
from core.types import PlaybackControls
from pyradios import RadioBrowser

logger = logging.getLogger(__name__)

STATIONS_PATH = Path(__file__).parent.parent / "radio" / "stations.json"
BASE_DIR = Path(__file__).resolve().parent.parent / "web" / "www"
ALBUM_IMAGES_WEB_PATH = Path("images") / "radio"

SQL_QUERY_SEARCH = {
    "radio": f"""
            SELECT 
                a.*
            FROM radio a
            WHERE %s
            ORDER BY a.name ASC
        """,
}
SQL_QUERY_CREATE = """
    CREATE TABLE IF NOT EXISTS radio (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        path        TEXT    NOT NULL UNIQUE,
        name        TEXT    NOT NULL,
        genre       TEXT,
        broadcaster TEXT,
        language    TEXT,
        country     TEXT,
        region      TEXT,
        bitrate     INTEGER,
        format      TEXT,
        home_page   TEXT,
        views       INTEGER NOT NULL DEFAULT 0,
        image       TEXT
    );
    """

SQL_QUERY_INSERT = """
    INSERT OR IGNORE INTO radio (
        path, name, genre, broadcaster, language,
        country, region, bitrate, format, home_page, image
    )
    VALUES (
        :path, :name, :genre, :broadcaster, :language,
        :country, :region, :bitrate, :format, :home_page, :image
    )
    """


class RadioExtension(SourceActor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config

        self._rb_instance = None
        
        self._source = Source(
            name="Radio",
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

    @property
    def rb(self):
        """
        Ein Property-Getter, der die RadioBrowser-Instanz erst erstellt, 
        wenn im Code über 'self.rb' darauf zugegriffen wird.
        """
        if self._rb_instance is None:
            try:
                # Versuche die Instanz erst jetzt zu erstellen
                self._rb_instance = RadioBrowser()
            except Exception as e:
                # Falls immer noch offline, loggen wir den Fehler, stürzen aber nicht ab
                print(f"[RadioPlugin] RadioBrowser konnte nicht initialisiert werden (Offline?): {e}")
                return None
        return self._rb_instance

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
        return self._source

    def _init_table(self):
        self._db.executescript(SQL_QUERY_CREATE)

    def _init_stations(self):
        with open(STATIONS_PATH, "r", encoding="utf-8") as f:
            radios = json.load(f)

        self._db.executemany(SQL_QUERY_INSERT, radios)
    

    def _build_track(self, row) -> any:
        obj = {
            "uri": f"radio:{row.path}",
            "name": row.name,
            "genre": row.genre or None,
        }

        if row.image:
            image_full_path = BASE_DIR / ALBUM_IMAGES_WEB_PATH / row.image
            image_path = ALBUM_IMAGES_WEB_PATH / row.image

            obj["images"] = (
                [Image(uri=str(image_path))] if image_full_path.is_file() else []
            )

        if row.country:
            obj["albums"] = frozenset([Album(name=row.country)])

        if row.broadcaster:
            obj["artists"] = frozenset([Artist(name=f"{row.genre} / {row.country}")])
        return obj

    def _build_track_rb(self, row, useUuidAsUri=True) -> dict:
        uuid = row.get("stationuuid")

        stream_url = row.get("url_resolved") or row.get("url") or ""
        
        uri = f"rbuuid-{uuid}" if useUuidAsUri else stream_url
        
        tags_str = row.get("tags", "")
        first_tag = tags_str.split(",")[0].strip() if tags_str else None

        obj = {
            "uri": f"radio:{uri}",
            "name": row.get("name", "Unbekannter Sender"),
            "genre": first_tag or "Radio",
        }

        if row.get("country"):
            obj["albums"] = frozenset([Album(name=row["country"])])
        
        if row.get("favicon"):
            obj["images"] = [Image(uri=str(row["favicon"]))]
        
        country_info = row.get("country", "Unknown")
        obj["artists"] = frozenset([Artist(name=f"{first_tag or 'Radio'} / {country_info}")])
        return obj

    def on_search(self, query: str) -> dict:
        sql = SQL_QUERY_SEARCH["radio"] % "a.name LIKE ? COLLATE NOCASE"
        rows = self._db.fetchall(sql, (f"%{query}%",))
        
        try:
            rowsBrowser = self.rb.search(name=query)
        except Exception as e:
            logger.error(f"Error during RadioBrowser query: {e}")
            rowsBrowser = []
        
        formattedRows = [Track(**self._build_track(row)) for row in rows]
        formattedRows.extend([Track(**self._build_track_rb(row)) for row in rowsBrowser])
        return {self._name : formattedRows}        


    async def on_lookup_track(self, path: str) -> Track:
        rows = self._db.fetchall("SELECT * FROM radio WHERE path = ?", (path,))
        if rows:
            return Track(**self._build_track(rows[0]))
        
        if path.startswith("rbuuid-"):
            try:
                uuid = path.split('-', 1)[1]
                rowsrb = self.rb.station_by_uuid(uuid)
                if rowsrb:
                    return Track(**self._build_track_rb(rowsrb[0], useUuidAsUri=False))
                else:
                    logger.warning(f"UUID {uuid} not found by RadioBrowser.")
            except Exception as e:
                logger.error(f"Error while resolving {path}: {e}")
        
        if path.startswith("http://") or path.startswith("https://"):
            return Track(
                uri=f"{self._name}:{path}",
                name="Internet Radio Stream",
                genre="Live Stream",
            )
        
        raise ValueError(f"Track with {path} could not be resolved locally or by RadioBrowser.")

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

        if values_len == 2:
            view, ref_id = values
            if str(ref_id).isdigit():
                raise ValueError("only alphabets allowed")
            else:
                rows = self._db.fetchall("""
                    SELECT a.*
                    FROM radio a
                    WHERE a.name LIKE ?
                    ORDER BY a.name ASC
                """, (f"{ref_id}%",))

        return [Track(**self._build_track(row)) for row in rows]

    async def on_playback_uri(self, path: str) -> any:
        #fetch url if uri is a radioBrowser item
        if path.startswith("rbuuid-"):
            try:
                uuid = path.split('-', 1)[1]
                rowsrb = self.rb.station_by_uuid(uuid)
                if rowsrb:
                    return rowsrb[0].get("url_resolved") or rowsrb[0].get("url")
            except Exception as e:
                logger.error(f"Error while getting playback URI for radio {path}: {e}")
                return None
        
        
        return path
