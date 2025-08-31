import { EVENTS } from "@/constants/events";

interface SystemState {
  datetime: string;
  power_state: { standby: boolean };
}

const initialState: SystemState = {
  datetime: "0000-00-00T00:00:00Z",
  power_state: { standby: true },
};

export const systemReducer = (
  state = initialState,
  action: any
): SystemState => {
  const { type, payload } = action;

  switch (type) {
    case EVENTS.SYSTEM_TIME_UPDATED:
      return { ...state, datetime: payload.datetime };
    case EVENTS.SYSTEM_POWER_STATE:  
    return { ...state, power_state: { ...payload.state } };
    default:
      return state;
  }
};
