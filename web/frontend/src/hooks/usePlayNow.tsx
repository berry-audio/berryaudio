import { useState } from "react";
import { REF } from "@/constants/refs";
import { useLocalService } from "@/services/local";
import { usePlaybackService } from "@/services/playback";
import { usePlaylistService } from "@/services/playlist";
import { useTracklistService } from "@/services/tracklist";
import { Ref, TlTrack, Track } from "@/types";

export function usePlayNow() {
  const { add, clear } = useTracklistService();
  const { getDirectory } = useLocalService();
  const { getPlaylistItem } = usePlaylistService();
  const { play, next } = usePlaybackService();

   const [loading, setLoading] = useState<boolean>(false);

  const handlePlayNow = async (item: Ref) => {
    setLoading(true);
    const tracksUris: string[] = [];
    switch (item.type) {
      case REF.DIRECTORY:
      case REF.ARTIST:
      case REF.ALBUM:
      case REF.GENRE: {
        const tracks = await getDirectory(`${item.uri}:list`);
        if (tracks.length) {
          tracksUris.push(...tracks.map((track: Track) => track.uri));
        }
        await play(tracksUris[0]);
        break;
      }
      case REF.PLAYLIST: {
        const playlist = await getPlaylistItem(item.uri);
        if (playlist.tracks.length) {
          tracksUris.push(
            ...playlist.tracks.map((track: TlTrack) => track.track.uri)
          );
        }
        await clear();
        await add(tracksUris);
        await next();
        await play();
        break;
      }
      default:
        tracksUris.push(item.uri);
        await play(tracksUris[0]);
        break;
    }
    setLoading(false);
  };

  return { handlePlayNow, loading };
}
