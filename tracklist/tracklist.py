import logging
import random

from core.actor import Actor
from core.util import generate_tlid
from core.models import TlTrack

logger = logging.getLogger(__name__)


class TracklistExtension(Actor):
    def __init__(self, name, core, db, config):
        """
        Initialize the tracklist extension.
        Keeps track of playback options (current queue, repeat, single, random),
        the current/next/previous track, and the tracklists (ordered and shuffled).
        Handles and skips to next track if we have playback errors
        """
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._repeat = False
        self._single = False
        self._random = False
        self._next_tltrack = None
        self._previous_tltrack = None
        self._current_tltrack = None
        self._playback_errors = 0
        self._tl_tracks: list[TlTrack] = []
        self._tl_tracks_shuffled: list[TlTrack] = []

    async def on_start(self) -> None:
        """Called when the extension starts up."""
        logger.info("Started")

    async def on_event(self, message) -> None:
        """
        Handle playback-related events.
        - track_playback_error → increment error counter
        - track_playback_ended → move to next track, unless all failed
        """
        if message["event"] == "track_playback_error":
            self._playback_errors += 1

        if message["event"] == "track_playback_ended":
            # if tlid = 0 then dont skip to next track
            # TODO
            if await self.on_next_track() is not None:
                if self._playback_errors >= len(self._tl_tracks):
                    logger.warning("All tracks failed to play, stopping.")
                    self._playback_errors = 0
                    return
                await self._core.request("playback.next", from_ui=False)
            else:
                self._playback_errors = 0

    async def on_stop(self) -> None:
        """Called when the extension is shutting down."""
        logger.info("Stopped")

    async def on_add(self, uris: list = []) -> bool:
        """
        Add tracks to the tracklist by URI.
        Requests playback track objects from extensions, wraps them in TlTrack,
        and appends them to the tracklist.
        """
        if uris:
            _tracks: list[TlTrack] = []
            for uri in uris:
                ext, track_id = uri.split(":")
                tl_track = await self._core.request(f"{ext}.lookup_track", id=track_id)
                next_track_tlid = generate_tlid()
                self._tl_tracks.append(TlTrack(next_track_tlid, track=tl_track))
                _tracks.append(TlTrack(next_track_tlid, track=tl_track))
            await self._init_shuffle()
            await self.on_next_track()
            self._playback_error = False
            self._core.send(
                target="web", event="tracklist_changed", tl_tracks=self._tl_tracks
            )
            return _tracks
        else:
            ValueError(f"No uris were provided")

    async def on_remove(self, tlid) -> list[TlTrack]:
        """
        Remove the matching tracks from the tracklist.

        """
        self._tl_tracks = [t for t in self._tl_tracks if t.tlid != tlid]
        self._core.send(
            target="web", event="tracklist_changed", tl_tracks=self._tl_tracks
        )
        return self._tl_tracks

    async def on_move(self, start: int, end: int, to_position: int) -> list[TlTrack]:
        """
        Move a slice of the tracklist (from start to end) to a new position.
        Validates boundaries before applying.
        """
        if start == end:
            end += 1

        tl_tracks = self._tl_tracks

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
        self._tl_tracks = new_tl_tracks
        await self.on_next_track()
        self._core.send(
            target="web", event="tracklist_changed", tl_tracks=self._tl_tracks
        )
        return True

    def on_get_tltracks(self) -> list[TlTrack]:
        """Return the current tracklist (not shuffled)."""
        return self._tl_tracks

    async def on_clear(self) -> bool:
        """
        Clear the tracklist and reset shuffled version as well.
        Also resets playback error state.
        """
        self._tl_tracks = []
        self._tl_tracks_shuffled = []
        await self.on_next_track()
        self._playback_error = False
        self._core.send(
            target="web", event="tracklist_changed", tl_tracks=self._tl_tracks
        )
        return True

    def on_get_repeat(self) -> bool:
        """Return whether repeat mode is enabled."""
        return self._repeat

    async def on_set_repeat(self, value: bool) -> bool:
        """Enable or disable repeat mode, and trigger option change event."""
        self._repeat = value
        await self.on_next_track()
        self._core.send(target="web", event="options_changed")
        return True

    def on_get_single(self) -> bool:
        """Return whether single mode is enabled."""
        return self._single

    async def on_set_single(self, value: bool) -> bool:
        """Enable or disable single mode, and trigger option change event."""
        self._single = value
        await self.on_next_track()
        self._core.send(target="web", event="options_changed")
        return True

    def on_get_random(self) -> bool:
        """Return whether shuffle (random) mode is enabled."""
        return self._random

    async def _init_shuffle(self) -> None:
        """
        Initialize or clear the shuffled version of the tracklist.
        Called when random mode is toggled or tracks are added.
        """
        if self._random:
            self._tl_tracks_shuffled = self._tl_tracks[:]
            random.shuffle(self._tl_tracks_shuffled)
        else:
            self._tl_tracks_shuffled = []
        await self.on_next_track()

    async def on_set_random(self, value: bool) -> bool:
        """Enable or disable shuffle, rebuild shuffled list, and trigger event."""
        self._random = value
        await self._init_shuffle()
        self._core.send(target="web", event="options_changed")
        return True

    def _get_index(self, tlid: int) -> int:
        """
        Get the index of a track by tlid.
        Uses the shuffled list if random is active, otherwise the normal list.
        """
        tracklist = self._tl_tracks_shuffled if self._random else self._tl_tracks
        for i, tl_track in enumerate(tracklist):
            if tl_track.tlid == tlid:
                return i
        return None

    async def on_next_track(self, from_ui: bool = False) -> TlTrack:
        """
        Advance to the next track.
        Handles repeat, single, and shuffle modes.
        Returns the next TlTrack or None if no track is available.
        """
        self._current_tltrack = await self._core.request(
            "playback.get_current_tl_track"
        )

        if not self._tl_tracks:
            return None

        tracklist = self._tl_tracks_shuffled if self._random else self._tl_tracks
        next_index = self._get_index(self._current_tltrack.tlid)

        if next_index is None:
            next_index = 0
        else:
            next_index += 1

        if self._repeat:
            next_index %= len(tracklist)

            if self._single:
                if from_ui:
                    await self.on_set_single({"value": False})
                else:
                    return self._current_tltrack

        elif next_index >= len(tracklist):
            self._next_tltrack = None
            return None

        self._next_tltrack = tracklist[next_index]
        return tracklist[next_index]

    async def on_previous_track(self, from_ui: bool = False) -> TlTrack:
        """
        Go back to the previous track.
        Respects single mode and shuffle setting.
        Returns the previous TlTrack or None if unavailable.
        """
        self._current_tltrack = await self._core.request(
            "playback.get_current_tl_track"
        )

        if not self._tl_tracks:
            return None

        tracklist = self._tl_tracks_shuffled if self._random else self._tl_tracks
        position = self._get_index(self._current_tltrack.tlid)

        if self._single:
            if from_ui:
                await self.on_set_single({"value": False})

        if position in (None, 0):
            return None

        self._previous_tltrack = tracklist[position - 1]
        return tracklist[position - 1]
