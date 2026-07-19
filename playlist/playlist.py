import logging
import json

from core.models import Playlist, TlTrack
from core.util import generate_tlid
from core.actor import Actor
from datetime import datetime

from .utils import build_tltrack, to_serialize

logger = logging.getLogger(__name__)
SQL_QUERY_CREATE =  """
            CREATE TABLE IF NOT EXISTS playlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                tracks TEXT NOT NULL,
                image TEXT,
                last_modified TEXT NOT NULL
            );
            """

class PlaylistExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config

    async def on_start(self):
        self._init_table()
        logger.info("Started")

    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")

    def _init_table(self):
        """Create the playlist table if it does not already exist."""
        self._db.executescript(SQL_QUERY_CREATE)

    def on_directory(
        self,
        uri: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        """
        Browse the playlist directory by URI.

        URI formats:
          - "playlist"              → list all playlists (paginated)
          - "playlist:{id}"         → fetch a single playlist by id
          - "playlist:{id}:tracks"  → fetch tracks belonging to a playlist
        """
        if not uri:
            raise ValueError("No 'uri' was defined.")

        values = uri.split(":")

        match len(values):
            case 3:
                view, ref_id, ref_type = values
                if view != self._name:
                    raise ValueError(f"View '{view}' not supported")
                if ref_type != "tracks":
                    raise ValueError(f"View type '{ref_type}' not supported")
                row = self._db.fetchone(f"SELECT * FROM playlist WHERE id = {ref_id}")
                result = []
                for t in json.loads(row.tracks):
                    obj = build_tltrack(t)
                    obj.uri = f"{view}:{ref_id}"
                    result.append(obj)
                return result

            case 2:
                view, ref_id = values
                row = self._db.fetchone(f"SELECT * FROM playlist WHERE id = {ref_id}")
                return Playlist(**self._build_playlist(row))

            case 1:
                sql = """
                    SELECT * FROM playlist
                    WHERE 1
                    ORDER BY last_modified DESC
                """
                params = []
                if limit is not None:
                    sql += " LIMIT ?"
                    params.append(limit)
                if offset is not None:
                    sql += " OFFSET ?"
                    params.append(offset)
                rows = self._db.fetchall(sql, params)
                return [Playlist(**self._build_playlist(row)) for row in rows]

            case _:
                raise ValueError(f"Invalid URI format: '{uri}'")

    def _build_playlist(self, row) -> dict:
        """Build a playlist dict from a database row, including track count."""
        return {
            "uri": f"playlist:{row.id}",
            "name": row.name,
            "length": len([build_tltrack(t) for t in json.loads(row.tracks)]),
            "last_modified": row.last_modified,
        }

    async def on_edit(self, uri: str, name: str) -> bool:
        """
        Rename a playlist by URI.
        """
        parts = uri.split(":")
        if len(parts) < 2:
            raise ValueError("Invalid URI format")

        playlist_id = int(parts[1])
        if not playlist_id:
            raise ValueError("id not provided")
        if not name:
            raise ValueError("name not provided")

        self._db.execute(
            "UPDATE playlist SET name = ? WHERE id = ?", (name, playlist_id)
        )
        logger.debug(f"{uri} updated")

        row = self._db.fetchone(f"SELECT * FROM playlist WHERE id = {playlist_id}")
        if not row:
            raise ValueError(f"Playlist {uri} not found")

        self._core.send(
            target=["web", "display"],
            event="playlist_renamed",
            playlist=Playlist(
                uri=uri,
                name=name,
                length=len(json.loads(row.tracks)),
                last_modified=row.last_modified,
            ),
        )
        return True

    async def on_delete(self, uri: str) -> bool:
        """
        Delete a playlist by URI.
        """
        parts = uri.split(":")
        if len(parts) < 2:
            raise ValueError("Invalid URI format")

        playlist_id = int(parts[1])
        if not playlist_id:
            raise ValueError("id not provided")

        row = self._db.fetchone(f"SELECT * FROM playlist WHERE id = {playlist_id}")
        if not row:
            raise ValueError(f"Playlist {uri} not found")

        self._db.execute("DELETE FROM playlist WHERE id = ?", (playlist_id,))
        logger.debug(f"{uri} removed")

        self._core.send(
            target=["web", "display"],
            event="playlist_removed",
            playlist=Playlist(
                uri=uri,
                name=row.name,
                length=len(json.loads(row.tracks)),
                last_modified=row.last_modified,
            ),
        )
        return True

    async def on_create(
        self, name: str | None = None, tl_tracks: list[TlTrack] | None = None
    ) -> bool:
        """
        Create a new playlist.
        If no name is given, generates one from the current timestamp.
        """
        playlist_tl_tracks = json.dumps(tl_tracks or [])
        last_modified = str(datetime.now().isoformat())
        playlist_name = name or f"Mix #{last_modified}"

        cursor = self._db.execute(
            "INSERT INTO playlist (name, tracks, last_modified) VALUES (?, ?, ?)",
            (playlist_name, playlist_tl_tracks, last_modified),
        )

        self._core.send(
            target=["web", "display"],
            event="playlist_created",
            playlist=Playlist(
                uri=f"playlist:{cursor.lastrowid}",
                name=playlist_name,
                length=len(tl_tracks),
                last_modified=last_modified,
            ),
        )
        return True

    async def on_move_track(
        self, uri: str, start: int, end: int, to_position: int
    ) -> bool:
        """
        Move a slice of tracks within a playlist to a new position.
        """
        playlist_id = int(uri.split(":")[1])
        row = self._db.fetchone(f"SELECT * FROM playlist WHERE id = {playlist_id}")
        tl_tracks = [build_tltrack(t) for t in json.loads(row.tracks)]

        if start == end:
            end += 1
        if start >= end:
            raise AssertionError("start must be smaller than end")
        if start < 0:
            raise AssertionError("start must be at least zero")
        if end > len(tl_tracks):
            raise AssertionError("end can not be larger than tracklist length")
        if to_position < 0:
            raise AssertionError("to_position must be at least zero")
        if to_position > len(tl_tracks):
            raise AssertionError("to_position can not be larger than tracklist length")

        new_tl_tracks = tl_tracks[:start] + tl_tracks[end:]
        for tl_track in tl_tracks[start:end]:
            new_tl_tracks.insert(to_position, tl_track)
            to_position += 1

        self._db.execute(
            "UPDATE playlist SET tracks = ? WHERE id = ?",
            (json.dumps(to_serialize(new_tl_tracks)), playlist_id),
        )
        self._core.send(
            target=["web", "display"],
            event="playlist_updated",
            playlist=Playlist(
                uri=uri,
                name=row.name,
                length=len(tl_tracks),
                last_modified=row.last_modified,
            ),
        )
        return True

    async def on_remove_track(self, uri: str, tlid: int) -> bool:
        """
        Remove a single track from a playlist by tlid.
        """
        parts = uri.split(":")
        if len(parts) < 2:
            raise ValueError("Invalid URI format")

        playlist_id = int(parts[1])
        if not playlist_id:
            raise ValueError("id not provided")
        if not tlid:
            raise ValueError("tlid not provided")

        row = self._db.fetchone(f"SELECT * FROM playlist WHERE id = {playlist_id}")
        if not row:
            raise ValueError(f"Playlist {uri} not found")

        tl_tracks = json.loads(row.tracks)
        tl_track = next((t for t in tl_tracks if t["tlid"] == tlid), None)
        if not tl_track:
            raise ValueError(f"Track {tlid} not found in playlist")

        tl_track["uri"] = uri
        tl_tracks_updated = [t for t in tl_tracks if t["tlid"] != tlid]

        self._db.execute(
            "UPDATE playlist SET tracks = ? WHERE id = ?",
            (json.dumps(tl_tracks_updated), playlist_id),
        )
        logger.debug(f"Track {tlid} removed from {uri}")
        self._core.send(
            target=["web", "display"],
            event="playlist_track_removed",
            tl_track=tl_track,
        )
        return True

    async def on_add_track(self, uris: list[str], track_uris: list[str]) -> bool:
        """
        Add one or more tracks to one or more playlists.
        """
        tracks = []
        for uri in track_uris:
            ext, file_path = uri.split(":", 1)
            track = await self._core.request(f"{ext}.lookup_track", path=file_path)
            tracks.append(track)

        for uri in uris:
            playlist_id = int(uri.split(":")[1])
            row = self._db.fetchone("SELECT * FROM playlist WHERE id = ?", (playlist_id,))
            tl_tracks = [build_tltrack(t) for t in json.loads(row.tracks)]
            tl_tracks_updated = []

            for track in tracks:
                tl_track = TlTrack(tlid=generate_tlid(), track=track)
                tl_tracks_updated.append(tl_track)
                tl_tracks.append(tl_track)

            self._db.execute(
                "UPDATE playlist SET tracks = ? WHERE id = ?",
                (json.dumps(to_serialize(tl_tracks)), playlist_id),
            )
            self._core.send(
                target=["web", "display"],
                event="playlist_track_added",
                tl_tracks=tl_tracks_updated,
            )
        return True