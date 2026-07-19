import logging
import ast

from core.actor import Actor
from core.models import Track
from playlist.utils import build_track, build_album, build_artist, to_serialize

logger = logging.getLogger(__name__)

SQL_QUERY_CREATE_FAVOURITE = """
    CREATE TABLE IF NOT EXISTS collection_favourite (
        uri            TEXT    PRIMARY KEY,
        model          TEXT,
        name           TEXT,
        item           TEXT
    );
    """
SQL_QUERY_CREATE_HISTORY = """
    CREATE TABLE IF NOT EXISTS collection_history (
        uri            TEXT    PRIMARY KEY,
        name           TEXT,
        track          TEXT,    
        last_played    TEXT,
        play_count     INTEGER NOT NULL DEFAULT 0
    );
    """


class CollectionExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db

    async def on_start(self):
        self._init_table()
        logger.info("Started")

    async def on_stop(self):
        logger.info("Stopped")

    async def on_event(self, message):
        pass

    def _init_table(self):
        self._db.executescript(SQL_QUERY_CREATE_FAVOURITE)
        self._db.executescript(SQL_QUERY_CREATE_HISTORY)

    def on_favourite(self, item) -> bool:
        uri = item.get("uri")
        name = item.get("name")
        cursor = self._db.execute(
            "SELECT 1 FROM collection_favourite WHERE uri = ?",
            (uri,),
        )
        row = cursor.fetchone()
        if row is None:
            self._db.execute(
                """
                INSERT INTO collection_favourite (uri, model, name, item)
                VALUES (?, ?, ?, ?)
                """,
                (uri, item.get("__model__"), name, str(to_serialize(item)),),
            )
            return True
        else:
            self._db.execute(
                "DELETE FROM collection_favourite WHERE uri = ?",
                (uri,),
            )
            return False

    def on_recently_played(self, track: Track) -> bool:
        self._db.execute(
            """
            INSERT INTO collection_history (uri, name, track, last_played, play_count)
            VALUES (?, ?, ?, datetime('now'), 1)
            ON CONFLICT(uri) DO UPDATE SET
                last_played = datetime('now'),
                play_count = play_count + 1
            """,
            (track.uri, track.name, str(to_serialize(track))),
        )
        return True

    async def on_directory(
        self,
        uri: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        params = []

        _, *parts = (uri or "").split(":")
        view = parts[0] if parts else None
        alpha = parts[1] if len(parts) > 1 else None

        if view == "favourite":
            sql = "SELECT * FROM collection_favourite"
        else:
            sql = "SELECT * FROM collection_history"

        if alpha:
            sql += " WHERE name LIKE ? COLLATE NOCASE"
            params.append(f"{alpha}%")

        if view == "recent":
            sql += " ORDER BY last_played DESC"
        elif view == "top100":
            sql += " ORDER BY play_count DESC"
        elif view == "favourite":
            sql += " ORDER BY name"

        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        if offset is not None:
            sql += " OFFSET ?"
            params.append(offset)

        rows = self._db.fetchall(sql, params)

        if view == "favourite":
            items = []
            for row in rows:
                model = row["model"]
                data = ast.literal_eval(row["item"])

                if model == "Track":
                    items.extend(build_track(data))
                elif model == "Album":
                    items.append(build_album(data))
                elif model == "Artist":
                    items.append(build_artist(data))

            return items
        
        return [
            track
            for row in rows
            for track in build_track(ast.literal_eval(row["track"]))
        ]

