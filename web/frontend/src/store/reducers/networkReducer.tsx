import { NetworkState } from "@/types";
import { INFO_EVENTS } from "../constants";
import { EVENTS } from "@/constants/events";

const initialState: NetworkState = {
  networks: [],
  devices: {},
};

export const networkReducer = (state = initialState, action: any): NetworkState => {
  const { type, payload } = action;

  switch (type) {
    case INFO_EVENTS.WLAN_SCAN_COMPLETED:
      return {
        ...state,
        networks: payload,
      };
    case EVENTS.NETWORK_DEVICES:
      return {
        ...state,
        devices: Object.fromEntries(payload.state.map((dev: string) => [dev, undefined])),
      };
    case EVENTS.NETWORK_STATE_CHANGED:
      return {
        ...state,
        devices: { ...state.devices, [payload.device.device]: payload.device },
        networks: payload.networks,
      };
    default:
      return state;
  }
};
