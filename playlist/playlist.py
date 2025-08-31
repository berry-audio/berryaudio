import logging
import json
import uuid

from core.models import RefType, Ref, Playlist, TlTrack
from core.util import generate_tlid
from core.actor import Actor
from datetime import datetime

from .utils import to_unserialize, to_serialize

logger = logging.getLogger(__name__)

class PlaylistExtension(Actor):
    def __init__(self, core, db, config):
        super().__init__()
        self._core = core
        self._db = db

    async def on_start(self):
        logger.info("Started")
        
    async def on_event(self, message):
        pass

    async def on_stop(self):
        logger.info("Stopped")


    def on_item(self, uri: str | None = None) -> Playlist | bool:
        id = int(uri.split(":")[1])
        if id:
            row = self._db.fetchone(f"SELECT * FROM playlist WHERE id = {id}")
            playlist = Playlist(
                    uri=f"playlist:{row.id}",
                    name=row.name, 
                    tracks=[to_unserialize(tlTrack) for tlTrack in json.loads(row.tracks)]
                )
            return playlist
        return False
    

    def on_directory(self,   
            uri: str | None = None, 
            limit: int | None = None, 
            offset: int | None = None
        ):
        if not uri:
            raise ValueError(f"No 'uri' was defined.")
        
        values = uri.split(":")
        values_len = len(values)

        if values_len and values_len == 1:
            base_sql =  f"""
                    SELECT 
                        a.*
                    FROM playlist a
                    WHERE %s
                    ORDER BY a.last_modified ASC
                """ % '1'
            sql = base_sql.rstrip(';')

            params = []
            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)

                if offset is not None:
                    sql += " OFFSET ?"
                    params.append(offset)

            rows = self._db.fetchall(sql, params)
        return [Ref(**self.build_playlist(row)) for row in rows]
    

    def build_playlist(self, row) -> any:
        obj = {
            "uri": f"playlist:{row.id}",
            "name": row.name,
            "type": RefType.PLAYLIST,
            "length": len([to_unserialize(tlTrack) for tlTrack in json.loads(row.tracks)]),
            "last_modified": row.last_modified
        }
        
        if row.image:
            pass
            # obj["images"] = [Image(uri=row.image or "/images/no_cover.jpg")]    
        return obj


    async def on_edit(self, uri: str, name: str) -> list[TlTrack]:
        id = int(uri.split(":")[1])
        if id and name:
            self._db.execute(
                "UPDATE playlist SET name = ? WHERE id = ?",
                (name, id)
            )
            logger.debug(f"{uri} updated")
            self._core.send(event='playlists_updated')
            return self.on_items()
        raise ValueError("id or name not provided")
    
        
    async def on_delete(self, uri: str) -> list[TlTrack]:
        id = int(uri.split(":")[1])
        if id:
            self._db.execute(
                "DELETE FROM playlist WHERE id = ?",
                (id,)
            )
            logger.debug(f"{uri} deleted")
            self._core.send(event='playlists_updated')
            return self.on_items()
    

    async def on_create(self, name: str | None = None, tl_tracks: list[TlTrack] | None = None) -> bool:
        tl_tracks   = json.dumps(tl_tracks or []) 
        last_modified = datetime.now().isoformat()
        playlist_name = name if name is not None else f"Mix #{last_modified}"

        self._db.execute(
            """INSERT INTO playlist (name, tracks, last_modified)
            VALUES (?, ?, ?)""",
            (
                playlist_name,
                tl_tracks,
                last_modified
            )
        )
        logger.debug(f"{playlist_name} created")
        self._core.send(event='playlists_updated')
        return True
       
       
    async def on_move(self, uri: str, start: int, end: int, to_position: int) -> list[TlTrack]:
        id = int(uri.split(":")[1])

        row = self._db.fetchone(f"SELECT * FROM playlist WHERE id = {id}")
        tl_tracks = [to_unserialize(tlTrack) for tlTrack in json.loads(row.tracks)]

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
                (json.dumps(to_serialize(new_tl_tracks)), id)
        )
        self._core.send(event='playlist_updated')
        return True
    

    async def on_remove(self, uri: str, tlid: int) -> list[TlTrack]:
        id = int(uri.split(":")[1])
        if id and tlid:
            row = self._db.fetchone(f"SELECT * FROM playlist WHERE id = {id}")
            tl_tracks = json.loads(row.tracks)
            tl_tracks_updated = [t for t in tl_tracks if t["tlid"] != tlid]
            self._db.execute(
                    "UPDATE playlist SET tracks = ? WHERE id = ?",
                    (json.dumps(tl_tracks_updated), id)
            )
            logger.debug(f"Track {tlid} removed from {uri}")
            self._core.send(event='playlist_updated')
            return self.on_item(uri)


    async def on_add(self, uris: list[str], track_uris: list[str]) -> bool:
        tracks = []

        for uri in track_uris:
            ext, track_id = uri.split(":")
            track = await self._core.request(f"{ext}.lookup_track", id=track_id)
            tracks.append(track)
        
        for uri in uris:
            playlist_id = int(uri.split(":")[1])
            row = self._db.fetchone("SELECT * FROM playlist WHERE id = ?", (playlist_id,))
            tl_tracks = [to_unserialize(tlTrack) for tlTrack in json.loads(row.tracks)]

            for track in tracks:
                tl_tracks.append(TlTrack(tlid=generate_tlid(), track=track))

            self._db.execute(
                    "UPDATE playlist SET tracks = ? WHERE id = ?",
                    (json.dumps(to_serialize(tl_tracks)), playlist_id)
            )    
        
        self._core.send(event='playlists_updated')
        return True