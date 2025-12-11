import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSourceService } from "@/services/source";
import { usePlaybackService } from "@/services/playback";
import { useTracklistService } from "@/services/tracklist";
import { useMixerService } from "@/services/mixer";
import { useSystemService } from "@/services/system";
import { useNetworkService } from "@/services/network";
import { EVENTS } from "@/constants/events";
import { Menu } from "../components/Menu";
import { getRepeatMode, getShuffleMode } from "@/util";

import Player from "@/components/Player";
import Spinner from "@/components/Spinner";
import OverlaySearch from "@/components/Overlay/OverlaySearch";
import OverlayNowPlaying from "@/components/Overlay/OverlayNowPlaying";
import OverlayLibrary from "@/components/Overlay/OverlayLibrary";
import OverlayStandby from "@/components/Overlay/OverlayStandby";
import OverlayOffline from "@/components/Overlay/OverlayOffline";
import Dialog from "@/components/Dialog";
import OverlayVolume from "@/components/Overlay/OverlayVolume";

export default function Layout({ children }: { children: any }) {
  const dispatch = useDispatch();
  const connected = useSelector((state: any) => state.socket.connected);

  const { getRepeat, getSingle, getRandom, getTracklist } = useTracklistService();
  const { getState, getCurrentTlTrack } = usePlaybackService();
  const { getMixerVolume, getMixerMute } = useMixerService();
  const { getSystemTime, getPowerState } = useSystemService();
  const { getDevices } = useNetworkService();
  const { getSource } = useSourceService();

  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!connected) return;

    const initialize = async () => {
      setLoading(true);
      try {
        const [
          _getNetworkDevices,
          _getPowerState,
          _getState,
          _getAudioSource,
          _tl_track,
          _tl_tracks,
          _value,
          _getRepeat,
          _getSingle,
          _getShuffle,
          _volume,
          _mute,
        ] = await Promise.all([
          getDevices(),
          getPowerState(),
          getState(),
          getSource(),
          getCurrentTlTrack(),
          getTracklist(),
          getSystemTime(),
          getRepeat(),
          getSingle(),
          getRandom(),
          getMixerVolume(),
          getMixerMute(),
        ]);

        dispatch({
          type: EVENTS.NETWORK_DEVICES,
          payload: { state: _getNetworkDevices },
        });

        dispatch({
          type: EVENTS.SYSTEM_POWER_STATE,
          payload: { state: _getPowerState },
        });

        dispatch({
          type: EVENTS.PLAYBACK_STATE_CHANGED,
          payload: { state: _getState },
        });

        dispatch({
          type: EVENTS.SOURCE_CHANGED,
          payload: { source: _getAudioSource },
        });

        dispatch({
          type: EVENTS.TRACK_META_UPDATED,
          payload: { tl_track: _tl_track },
        });

        dispatch({
          type: EVENTS.TRACKLIST_CHANGED,
          payload: { tl_tracks: _tl_tracks },
        });

        dispatch({
          type: EVENTS.SYSTEM_TIME_UPDATED,
          payload: { datetime: _value },
        });

        dispatch({
          type: EVENTS.VOLUME_CHANGED,
          payload: { volume: _volume },
        });

        dispatch({
          type: EVENTS.MIXER_MUTE,
          payload: { mute: _mute },
        });

        dispatch({
          type: EVENTS.OPTIONS_CHANGED,
          payload: {
            repeat_mode: getRepeatMode(_getRepeat, _getSingle),
            shuffle_mode: getShuffleMode(_getShuffle),
          },
        });
      } catch (err) {
        console.error("Error initiazing:", err);
      } finally {
        setLoading(false);
      }
    };

    initialize();
  }, [connected]);

  return loading ? (
    <Spinner />
  ) : (
    <>
      <div className="flex flex-col h-full dark:bg-[#141414] relative bg-neutral-100">
        <Menu />
        <div className="flex-1 overflow-hidden">{children}</div>
        <Player />
      </div>
      <Dialog />
      <OverlaySearch />
      <OverlayNowPlaying />
      <OverlayLibrary />
      <OverlayStandby />
      <OverlayOffline />
      <OverlayVolume />
    </>
  );
}
