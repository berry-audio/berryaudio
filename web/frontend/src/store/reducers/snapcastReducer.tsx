import { SnapcastState } from "@/types";
import { INFO_EVENTS } from "../constants";
import { EVENTS } from "@/constants/events";

const initialState: SnapcastState = {
  status: {
        "clients": [],
        "server": [],
        "streams": []
    },
  servers_available: [],
};

export const snapcastReducer = (state = initialState, action: any): SnapcastState => {
  const { type, payload } = action;

  switch (type) {
    case INFO_EVENTS.SNAPCAST_SCAN_COMPLETED:
      return {
              ...state,
              servers_available: payload,
            };
    case EVENTS.SNAPCAST_STATE_CHANGED:
            return { ...state, servers_available: payload.servers };
    default:
      return state;
  }
};