import { INFO_EVENTS } from "../constants";

interface EventState {
  event: string | null;
  payload: any;
}

const initialDialogState: EventState = {
  event: null,
  payload: null,
};

export const eventReducer = (state = initialDialogState, action: any): EventState => {
  const { type } = action;

  switch (type) {
    case INFO_EVENTS.PLAYLISTS_UPDATED:
      return {
        event: type,
        payload: null,
      };
    default:
      return state;
  }
};