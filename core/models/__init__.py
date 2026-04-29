from __future__ import annotations

import enum
from collections.abc import Iterator
from typing import Literal, NewType, TypeAlias, Optional

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
    TRACK = "track"
    DIRECTORY = "directory"
    CATEGORY = "category"
    PLAYLIST = "playlist"
    STORAGE = "storage"
    INTERNAL = "internal"
    BLUETOOTH = "bluetooth"
    REMOVABLE = "removable"
    NAS = "nas"

    def __repr__(self) -> str:
        return self.name


class Album(BaseModel):
    """Represents a musical album."""

    model: Literal["Album"] = Field(
        default="Album",
        repr=False,
        alias="__model__",
    )
    uri: str | None = None
    name: str | None = None
    artists: frozenset[Artist] = frozenset()
    num_tracks: NonNegativeInt | None = None
    num_discs: NonNegativeInt | None = None
    date: int | None = None
    musicbrainz_id: UUID | None = None
    images: tuple | None = None


class Artist(BaseModel):
    """Represents a musical artist."""

    model: Literal["Artist"] = Field(
        default="Artist",
        repr=False,
        alias="__model__",
    )
    uri: str | None = None
    name: str | None = None
    sortname: str | None = None
    albums: frozenset[Album] = frozenset()
    musicbrainz_id: UUID | None = None
    images: tuple | None = None


class Category(BaseModel):
    """Represents a genre."""

    model: Literal["Category"] = Field(
        default="Category",
        repr=False,
        alias="__model__",
    )
    uri: str | None = None
    name: str | None = None


Album.model_rebuild()
Artist.model_rebuild()


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
    bit_depth: str | None = None
    size: Optional[int] = None


class Tuner(BaseModel):
    model_config = ConfigDict(frozen=False)
    model: Literal["Tuner"] = Field(default="Tuner", alias="__model__", repr=False)
    uri: str
    name: Optional[str] = None
    frequency: int = 0
    audio_codec: str | None = None
    channels: NonNegativeInt | None = None
    sample_rate: NonNegativeInt | None = None
    bit_depth: str | None = None


class TlTrack(BaseModel):
    model_config = ConfigDict(frozen=False)
    model: Literal["TlTrack"] = Field(default="TlTrack", repr=False, alias="__model__")
    uri: Optional[str] = None
    tlid: str | int
    track: Track | Tuner

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
    length: Optional[int] = 0
    last_modified: str | None = None


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
    model: Literal["Source"] = Field(default="Source", alias="__model__", repr=False)
    name: Optional[str] = None
    uri: Optional[Uri] = None
    active: bool = False
    controls: list[str] = Field(default_factory=list)
    state: State = Field(default_factory=State)


class StorageUsage(BaseModel):
    total: Optional[int] = None
    used: Optional[int] = None
    free: Optional[int] = None


class Storage(BaseModel):
    model_config = ConfigDict(frozen=False)
    model: Literal["Storage"] = Field(default="Storage", alias="__model__", repr=False)
    icon: RefType = RefType.STORAGE
    uri: Optional[str] = None
    name: Optional[str] = None
    dev: Optional[str] = None
    shared: bool = False
    fstype: Optional[str] = None
    size: int = 0
    status: Optional[str] = None
    usage: Optional[StorageUsage] = None
    read_only: bool = False
    guest_allowed: bool = True
    user: Optional[str] = None
    create_permissions: Optional[str] = None
    directory_permissions: Optional[str] = None


class Directory(BaseModel):
    model_config = ConfigDict(frozen=False)
    model: Literal["Directory"] = Field(
        default="Directory", alias="__model__", repr=False
    )
    uri: str
    name: str
    shared: bool = False
    user: Optional[str] = None
    read_only: bool = False
    guest_allowed: bool = True
    user: Optional[str] = None
    create_permissions: Optional[str] = None
    directory_permissions: Optional[str] = None


class File(BaseModel):
    model_config = ConfigDict(frozen=False)
    model: Literal["File"] = Field(default="File", alias="__model__", repr=False)
    uri: str
    name: str
    size: int = 0
    ext: str


class Bluetooth(BaseModel):
    model_config = ConfigDict(frozen=False)
    model: Literal["Bluetooth"] = Field(
        default="Bluetooth", alias="__model__", repr=False
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


class Room(BaseModel):
    model_config = ConfigDict(frozen=False)

    model: Literal["Room"] = Field(default="Room", alias="__model__", repr=False)
    service_name: Optional[str] = None
    name: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    connected: Optional[bool] = None
    status: Optional[str] = None
