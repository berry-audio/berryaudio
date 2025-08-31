import { useDispatch } from "react-redux";
import { DIALOG_EVENTS } from "@/store/constants";
import { Ref } from "@/types";

export function useLibraryInfo() {
  const dispatch = useDispatch();

  const handleArtistInfo = (item: Ref) => {
    dispatch({ type: DIALOG_EVENTS.DIALOG_INFO_LIBRARY, payload: item });
  };

  return { handleArtistInfo };
}
