import enum
from collections.abc import Iterator
from typing import Any, ClassVar, Literal, Self, NewType, TypeAlias, Optional

from pydantic import Field, ConfigDict
from pydantic.fields import Field
from pydantic.types import UUID, NonNegativeInt
from core.models._base import BaseModel

Date = NewType("Date", str)
Year = NewType("Year", str)
DateOrYear = Date | Year

DurationMs = NewType("DurationMs", int)
Uri = NewType("Uri", str)

TracklistId = NewType("TracklistId", int)
TracklistField: TypeAlias = Literal[
    "tlid",
    "uri",
    "name",
    "genre",
    "comment",
    "musicbrainz_id",
]


class RefType(enum.StrEnum):
    """Enumeration of reference types used for tracks, albums, artists, etc."""

    ALBUM = "album"
    ARTIST = "artist"
    DIRECTORY = "directory"
    PLAYLIST = "playlist"
    TRACK = "track"
    SOURCE = "source"
    STORAGE = "storage"
    BLUETOOTH = "bluetooth"

    def __repr__(self) -> str:
        return self.name


class Artist(BaseModel):
    """Represents a musical artist."""

    model: Literal["Artist"] = Field(
        default="Artist",
        repr=False,
        alias="__model__",
    )
    uri: Uri | None = None
    name: str | None = None
    sortname: str | None = None
    musicbrainz_id: UUID | None = None
    images: tuple | None = None


class Album(BaseModel):
    """Represents a musical album."""

    model: Literal["Album"] = Field(
        default="Album",
        repr=False,
        alias="__model__",
    )
    uri: Uri | None = None
    name: str | None = None
    artists: frozenset[Artist] = frozenset()
    num_tracks: NonNegativeInt | None = None
    num_discs: NonNegativeInt | None = None
    date: int | None = None
    musicbrainz_id: UUID | None = None
    images: tuple | None = None


class Image(BaseModel):
    """Represents an image with URI and optional dimensions."""

    model: Literal["Image"] = Field(
        default="Image",
        repr=False,
        alias="__model__",
    )
    uri: Uri
    width: NonNegativeInt | None = None
    height: NonNegativeInt | None = None


class Track(BaseModel):
    """Represents a musical track."""

    model: Literal["Track"] = Field(
        default="Track",
        repr=False,
        alias="__model__",
    )
    uri: Uri | None = None
    name: str | None = None
    artists: frozenset[Artist] = frozenset()
    albums: frozenset[Album] = frozenset()
    composers: frozenset[Artist] = frozenset()
    performers: frozenset[Artist] = frozenset()
    genre: str | None = None
    track_no: NonNegativeInt | None = None
    disc_no: NonNegativeInt | None = None
    date: DateOrYear | int | None = Field(
        default=None,
        pattern=r"^\d{4}(-\d{2}-\d{2})?$",
    )
    length: DurationMs | None = None
    bitrate: NonNegativeInt | None = None
    comment: str | None = None
    musicbrainz_id: UUID | None = None
    images: tuple | None = None
    last_modified: NonNegativeInt | None = None
    sample_rate: NonNegativeInt | None = None
    audio_codec: str | None = None
    channels: NonNegativeInt | None = None
    bit_depth: str = None
    resample: bool = None


class TlTrack(BaseModel):
    """Represents a musical track in queue"""

    model: Literal["TlTrack"] = Field(
        default="TlTrack",
        repr=False,
        alias="__model__",
    )

    tlid: str | int
    track: Track

    def __init__(
        self,
        tlid: str | int,
        track: Track,
        **_: Any,
    ) -> None:
        super().__init__(tlid=tlid, track=track)

    def __iter__(self) -> Iterator[TracklistId | Track]:
        return iter((self.tlid, self.track))


class Playlist(BaseModel):
    model: Literal["Playlist"] = Field(
        default="Playlist",
        repr=False,
        alias="__model__",
    )
    uri: str | None = None
    name: str | None = None
    tracks: tuple[TlTrack, ...] = ()
    last_modified: NonNegativeInt | None = None


class Ref(BaseModel):
    """Lightweight reference to an object with URI, type, and optional metadata."""

    model: Literal["Ref"] = Field(
        default="Ref",
        repr=False,
        alias="__model__",
    )
    uri: Uri
    name: str | None = None
    type: RefType
    artists: frozenset[Artist] = frozenset()
    albums: frozenset[Album] = frozenset()
    composers: frozenset[Artist] = frozenset()
    performers: frozenset[Artist] = frozenset()
    genre: str | None = None
    country: str | None = None
    track_no: NonNegativeInt | None = None
    disc_no: NonNegativeInt | None = None
    date: int | None = None
    length: DurationMs | None = None
    bitrate: NonNegativeInt | None = None
    comment: str | None = None
    musicbrainz_id: UUID | None = None
    last_modified: str | None = None
    images: tuple | None = None


class State(BaseModel):
    model_config = ConfigDict(frozen=False)
    connected: bool = False
    user_name: Optional[str] = None
    connection_id: Optional[str] = None
    name: Optional[str] = None
    icon: Optional[str] = None
    address: Optional[str] = None


class Source(BaseModel):
    model_config = ConfigDict(frozen=False)
    model: Literal["Source"] = Field(
        default="Source", 
        alias="__model__", 
        repr=False
        )
    name: Optional[str] = None
    type: Optional[str] = None
    uri: Optional[Uri] = None
    active: bool = False
    controls: list[str] = Field(default_factory=list)
    state: State = Field(default_factory=State)


class Storage(BaseModel):
    model_config = ConfigDict(frozen=False)
    model: Literal["Storage"] = Field(
        default="Storage", 
        alias="__model__", 
        repr=False
        )
    dev: Optional[str] = None
    parent: Optional[str] = None
    type: Optional[str] = None
    removable: Optional[bool] = None
    size: Optional[int] = None
    marketed_gb: Optional[int] = None
    fstype: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    uri: Optional[str] = None
    total: Optional[int] = None
    used: Optional[int] = None
    free: Optional[int] = None
    percent: Optional[float] = None


class Bluetooth(BaseModel):
    model_config = ConfigDict(frozen=False)
    model: Literal["Bluetooth"] = Field(
        default="Bluetooth", 
        alias="__model__", 
        repr=False
    )
    address: Optional[str] = None
    name: Optional[str] = None
    type: Optional[RefType] = None
    profile: Optional[str] = None
    alias: Optional[str] = None
    icon: Optional[str] = None
    paired: Optional[bool] = None
    trusted: Optional[bool] = None
    connected: Optional[bool] = None
    soft_volume: Optional[bool] = None
    volume: Optional[int] = None
    channels: Optional[int] = None
    audio_codec: Optional[str] = None
    sample_rate: Optional[int] = None
    bit_depth: Optional[str] = None
    uuids: Optional[list[str]] = None

class Snapcast(BaseModel):
    model_config = ConfigDict(frozen=False)
    
    model: Literal["Snapcast"] = Field(
        default="Snapcast",
        alias="__model__",
        repr=False
    )
    service_name: Optional[str] = None
    name: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    connected: Optional[bool] = None
    status: Optional[str] = None