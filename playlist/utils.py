from core.models import Image, Album, Artist, Track, TlTrack


def build_artist(obj):
    return Artist(
        uri=obj.get("uri"),
        name=obj.get("name"),
        sortname=obj.get("sortname"),
        musicbrainz_id=obj.get("musicbrainz_id"),
        images=tuple(build_image(i) for i in obj.get("images", []) or []),
    )


def build_image(obj):
    return Image(uri=obj.get("uri"), width=obj.get("width"), height=obj.get("height"))


def build_album(obj):
    return Album(
        uri=obj.get("uri"),
        name=obj.get("name"),
        artists=frozenset(build_artist(a) for a in obj.get("artists", [])),
        images=tuple(build_image(i) for i in obj.get("images", []) or []),
        num_tracks=obj.get("num_tracks"),
        num_discs=obj.get("num_discs"),
        date=obj.get("date"),
        musicbrainz_id=obj.get("musicbrainz_id"),
    )


def build_tltrack(tlTrack):
    track = tlTrack.get("track")
    return TlTrack(
        tlid=tlTrack.get("tlid"),
        track=Track(
            uri=track.get("uri"),
            name=track.get("name"),
            artists=frozenset(build_artist(a) for a in track.get("artists", [])),
            albums=frozenset(build_album(a) for a in track.get("albums", [])),
            genre=track.get("genre"),
            track_no=track.get("track_no"),
            disc_no=track.get("disc_no"),
            date=track.get("date"),
            length=track.get("length"),
            bitrate=track.get("bitrate"),
            images=(
                tuple(build_image(i) for i in track["images"])
                if track.get("images") is not None
                else []
            ),
        ),
    )

def build_track(_Track):
    return Track(
            uri=_Track.get("uri"),
            name=_Track.get("name"),
            artists=frozenset(build_artist(a) for a in _Track.get("artists", [])),
            albums=frozenset(build_album(a) for a in _Track.get("albums", [])),
            genre=_Track.get("genre"),
            track_no=_Track.get("track_no"),
            disc_no=_Track.get("disc_no"),
            date=_Track.get("date"),
            length=_Track.get("length"),
            bitrate=_Track.get("bitrate"),
            images=(
                tuple(build_image(i) for i in _Track["images"])
                if _Track.get("images") is not None
                else []
            ),
        ),

def to_serialize(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, (set, frozenset, tuple, list)):
        return [to_serialize(x) for x in obj]

    if isinstance(obj, dict):
        return {k: to_serialize(v) for k, v in obj.items()}

    if hasattr(obj, "_asdict"):
        return {k: to_serialize(v) for k, v in obj._asdict().items()}
    if hasattr(obj, "__dict__"):
        return {k: to_serialize(v) for k, v in vars(obj).items()}

    return str(obj)
