import enum
from typing import TYPE_CHECKING, Literal, NewType, TypeVar



class PlaybackState(enum.StrEnum):
    """Enum of playback states."""

    #: Constant representing the paused state.
    PAUSED = "paused"

    #: Constant representing the playing state.
    PLAYING = "playing"

    #: Constant representing the stopped state.
    STOPPED = "stopped"


class PlaybackControls(enum.StrEnum):
    """Enum of playback control states."""
    PLAY = "play"
    PAUSE = "pause"
    STOP = "stop"    
    NEXT = "next"    
    PREVIOUS = "previous"    
    REPEAT = "repeat"    
    SHUFFLE = "shuffle"    
    SEEK = "seek"    