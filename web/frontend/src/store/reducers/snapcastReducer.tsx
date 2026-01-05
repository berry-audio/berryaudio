import { SnapcastState } from "@/types";
import { INFO_EVENTS } from "../constants";
import { EVENTS } from "@/constants/events";

const initialState: SnapcastState = {
  status: {},
  servers: [],
};

export const snapcastReducer = (state = initialState, action: any): SnapcastState => {
  const { type, payload } = action;

  switch (type) {
    case INFO_EVENTS.SNAPCAST_SCAN_COMPLETED:
      return {
        ...state,
        servers: payload,
      };
      
    case EVENTS.SNAPCAST_STATE_CHANGED:
      return { ...state, status: payload.status };

    case EVENTS.SNAPCAST_CONNECTED:
    case EVENTS.SNAPCAST_DISCONNECTED:
      return {
        ...state,
        servers: [...state.servers.filter((server) => server?.ip !== payload.server?.ip), payload.server],
      };

    case EVENTS.SNAPCAST_NOTIFICATION:
      if (payload.method === "Stream.OnUpdate") {
        return {
          ...state,
          servers: state.servers.map((server) => (server?.connected ? { ...server, status: payload.params.stream.status } : server)),
        };
      }
      return state;
    default:
      return state;
  }
};
