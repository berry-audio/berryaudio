import { PLAYER_EVENTS } from "../constants";
import { PLAYBACK_STATE, REPEAT_MODE, SHUFFLE_MODE } from "@/constants/states";
import { EVENTS } from "@/constants/events";
import { MediaPlayer, Source } from "@/types";

const initialSource: Source = {
  type: "none",
  controls: [],
  state: { connected: false },
};

const initialMediaPlayer: MediaPlayer = {
  source: initialSource,
  playback_state: PLAYBACK_STATE.STOPPED,
  repeat_mode: REPEAT_MODE.REPEAT_OFF,
  shuffle_mode: SHUFFLE_MODE.SHUFFLE_OFF,
  volume: 0,
  mute: false,
  elapsed_ms: 0,
  current_track_cover: undefined,
  current_track: {
    __model__: "TlTrack",
    tlid: 0,
    track: {
      __model__: "Track",
      uri: "",
      name: "",
      artists: [],
      album: {
        __model__: "Album",
        uri: "",
        name: "",
        artists: [],
        num_tracks: null,
        num_discs: null,
        date: "",
        musicbrainz_id: null,
      },
      composers: [],
      performers: [],
      genre: "",
      track_no: 0,
      disc_no: 0,
      date: "",
      length: 0,
      bitrate: 0,
      comment: "",
      musicbrainz_id: null,
      last_modified: 0,
      images: [],
      sample_rate: 0,
      audio_codec: "",
      channels: 0,
      bit_depth: "",
    },
  },
  current_playlist: [],
  current_playlist_loading: false,
  is_standby: false,
};

export const playerReducer = (
  state = initialMediaPlayer,
  action: any
): MediaPlayer => {
  const { type, payload } = action;

  switch (type) {
    case PLAYER_EVENTS.POSITION_UPDATED:
      return {
        ...state,
        elapsed_ms: payload,
      };

    case EVENTS.SOURCE_CHANGED:
      return { ...state, source: { ...payload.source } };

    case EVENTS.SOURCE_UPDATED:
      return { ...state, source: { ...payload.source } };

    case EVENTS.TRACK_META_UPDATED:
      return { ...state, current_track: payload.tl_track };

    case EVENTS.PLAYBACK_STATE_CHANGED:
      return { ...state, playback_state: payload.state };

    case EVENTS.TRACKLIST_CHANGED:
      return { ...state, current_playlist: payload.tl_tracks };

    case EVENTS.TRACK_PLAYBACK_STARTED:
    case EVENTS.TRACK_PLAYBACK_PAUSED:
    case EVENTS.TRACK_PLAYBACK_RESUMED:
      return {
        ...state,
        elapsed_ms: payload.time_position,
        current_track: payload.tl_track,
      };

    case EVENTS.TRACK_PLAYBACK_ENDED:
      return {
        ...state,
        elapsed_ms: 0,
        current_track: payload.tl_track,
      };

    case EVENTS.VOLUME_CHANGED:
      return {
        ...state,
        volume: payload.volume,
      };
    case EVENTS.MIXER_MUTE:
      return {
        ...state,
        mute: payload.mute,
      };  
    case EVENTS.OPTIONS_CHANGED:
      return {
        // todo
        ...state,
      };

    default:
      return state;
  }
};
