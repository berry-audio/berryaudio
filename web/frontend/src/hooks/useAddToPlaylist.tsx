import { useDispatch } from "react-redux";
import { Ref } from "@/types";
import { DIALOG_EVENTS } from "@/store/constants";

export function useAddToPlaylist() {
  const dispatch = useDispatch();

  const handleAddToPlaylist = (item: Ref) => {
    dispatch({ type: DIALOG_EVENTS.DIALOG_PLAYLISTS, payload: item });
  };

  return { handleAddToPlaylist };
}
