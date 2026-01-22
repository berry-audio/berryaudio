import { useDispatch, useSelector } from "react-redux";
import { OVERLAY_EVENTS } from "@/store/constants";

export function usePlayerActions() {
  const dispatch = useDispatch();
  const { source } = useSelector((state: any) => state.player);

  const openNowPlayingOverlay = () => {
    if (!source.type) return;
    dispatch({ type: OVERLAY_EVENTS.OVERLAY_NOWPLAYING });
  };

  return { openNowPlayingOverlay };
}
