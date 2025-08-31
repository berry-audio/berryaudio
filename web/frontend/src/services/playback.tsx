import { useSocketRequest } from "@/store/useSocketRequest";

export const usePlaybackService = () => {
  const { request } = useSocketRequest();

  return {
    setSeek: (time_position: number) =>
      request("playback.seek", { time_position }),
    getCurrentTlTrack: () => request("playback.get_current_tl_track"),
    getCurrentTrackPos: () => request("playback.get_time_position"),
    getState: () => request("playback.get_state"),
    play: (uri?: string, tlid?:number) => request("playback.play", { uri, tlid }),
    pause: () => request("playback.pause"),
    resume: () => request("playback.resume"),
    stop: () => request("playback.stop"),
    next: () => request("playback.next"),
    prev: () => request("playback.previous"),
  };
};
