import { NetworkState } from "@/types";
import { INFO_EVENTS } from "../constants";

const initialState: NetworkState = {
  networks: [],
  wlan0: undefined,
  eth0: undefined,
};

export const networkReducer = (
  state = initialState,
  action: any
): NetworkState => {
  const { type, payload } = action;

  switch (type) {
    case INFO_EVENTS.SCAN_WIFI_COMPLETED:
      return {
        ...state,
        networks: payload,
      };
    default:
      return state;
  }
};
