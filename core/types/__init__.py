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

class GpioActions(enum.StrEnum):
    """Enum of GPIO remote control actions."""
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    MUTE = "mute"
    STANDBY = "standby"
    UP = "up"
    DOWN = "down"
    SELECT = "select"
    BACK = "back"
    DIRECTORY = "directory"
    VISUALISER = "visualiser"
    PLAY_PAUSE = "play_pause"
    STOP = "stop"
    NEXT = "next"
    PREVIOUS = "previous"
    MEMORY = "memory"
    SOURCE = "source"
    EQUALISER = "equaliser"
    NOW_PLAYING = "now_playing"

class EncoderMode(enum.StrEnum):
    VOLUME = "volume"
    DIRECTION = "direction"

class DisplayPage(enum.StrEnum):
    STANDBY = "standby"
    SOURCE = "source"
    SOURCE_DIRECTORY = "source_directory"    
    NOW_PLAYING = "now_playing"    
    DIRECTORY = "directory"    
    POWER_STATE_CHANGING = "power_state_changing"    
    MUTE = "mute"    
    VOLUME = "volume"    
    LOADING = "loading"