import { useSocketRequest } from "@/store/useSocketRequest";

export const useTracklistService = () => {
  const { request } = useSocketRequest();

  return {
    getRepeat: () => request("tracklist.get_repeat"),
    setRepeat: (value: boolean) => request("tracklist.set_repeat", { value }),
    getSingle: () => request("tracklist.get_single"),
    setSingle: (value: boolean) => request("tracklist.set_single", { value }),
    getRandom: () => request("tracklist.get_random"),
    setRandom: (value: boolean) => request("tracklist.set_random", { value }),
    getTracklist: () => request("tracklist.get_tltracks"),
    move: (start: number, end: number, to_position: number) =>
      request("tracklist.move", {
        start,
        end,
        to_position,
      }),
    remove: (tlid: any) => request("tracklist.remove", { tlid }),
    clear: () => request("tracklist.clear"),
    add: (value: string[]) => request("tracklist.add", { uris: value }),
  };
};
