import { OVERLAY_EVENTS } from "../constants";

interface OverlayState {
  overlay: string | null;
  payload: any;
}

const initialOverlayState: OverlayState = {
  overlay: null,
  payload: null,
};

export const overlayReducer = (
  state = initialOverlayState,
  action: any
): OverlayState => {
  const { type, payload } = action;

  switch (type) {
    case OVERLAY_EVENTS.OVERLAY_SEARCH:
    case OVERLAY_EVENTS.OVERLAY_NOWPLAYING:
    case OVERLAY_EVENTS.OVERLAY_STANDBY:
    case OVERLAY_EVENTS.OVERLAY_VOLUME:
      return {
        overlay: type,
        payload: null,
      };

    case OVERLAY_EVENTS.OVERLAY_LIBRARY:
      return {
        overlay: OVERLAY_EVENTS.OVERLAY_LIBRARY,
        payload: payload,
      };

    case OVERLAY_EVENTS.OVERLAY_CLOSE:
      return {
        overlay: null,
        payload: null,
      };

    default:
      return state;
  }
};
