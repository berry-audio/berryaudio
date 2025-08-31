import { TlTrack } from "@/types";
import { useSocketRequest } from "@/store/useSocketRequest";

export const usePlaylistService = () => {
  const { request } = useSocketRequest();

  return {
    getDirectory: (uri?: string, limit?: number, offset?:number) => request("playlist.directory", {uri, limit, offset}),
    getPlaylistItem: (uri: string) => request("playlist.item", { uri }),
    createItem: (name?: string, tl_tracks?: TlTrack[]) => request("playlist.create", { name, tl_tracks }),
    editItem: (uri: string, name: string) => request("playlist.edit", { uri, name }),
    deleteItem: (uri: string) => request("playlist.delete", { uri }),
    move: (uri: string, start: number, end: number, to_position: number) =>
      request("playlist.move", {
        uri,
        start,
        end,
        to_position,
      }),
    remove: (uri: string, tlid: number) =>
      request("playlist.remove", { uri, tlid }),
    onAdd: (uris: string[], track_uris: string[]) =>
      request("playlist.add", { uris, track_uris }),
  };
};
