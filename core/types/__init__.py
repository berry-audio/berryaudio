import enum


class PlaybackState(enum.StrEnum):
    """Enum of playback states."""

    PAUSED = "paused"
    PLAYING = "playing"
    STOPPED = "stopped"
    READY = "ready"
    BUFFERING = "buffering"
    UNKNOWN = "unknown"


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
    FAVOURITE = "favourite"


class Command(enum.StrEnum):
    """Enum of GPIO remote control actions."""

    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    MUTE = "mute"
    STANDBY = "standby"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    LEFT_LONG = "left_long"
    RIGHT = "right"
    RIGHT_LONG = "right_long"
    SELECT = "select"
    SELECT_LONG = "select_long"
    BACK = "back"
    BACK_LONG = "back_long"
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
    """Enum encoder modes."""

    VOLUME = "volume"
    DIRECTION = "direction"


class DisplayPage(enum.StrEnum):
    """Enum of display screens."""

    STANDBY = "standby"
    SOURCE = "source"
    SOURCE_DIRECTORY = "source_directory"
    NOW_PLAYING = "now_playing"
    DIRECTORY = "directory"
    POWER_STATE_CHANGING = "power_state_changing"
    MUTE = "mute"
    VOLUME = "volume"
    LOADING = "loading"
    POWER = "power"
    TRACKLIST = "tracklist"
