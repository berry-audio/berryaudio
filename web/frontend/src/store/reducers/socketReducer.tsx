import { SOCKET_EVENTS } from "../constants";

const initialState = { event: null, payload: null };

export const socketReducer = (state = initialState, action: any) => {
  const { type, payload } = action;

  switch (type) {
    case SOCKET_EVENTS.SOCKET_CONNECTED:
      return { connected: true };
    case SOCKET_EVENTS.SOCKET_DISCONNECTED:
      return { connected: false };
    case SOCKET_EVENTS.SOCKET_EVENT:
      return { ...state, payload: payload };
    default:
      return state;
  }
};
