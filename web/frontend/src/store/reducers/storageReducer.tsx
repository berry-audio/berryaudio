import { EVENTS } from "@/constants/events";

interface StorageState {
  storage: any;
}

const initialState: StorageState = {
  storage: {},
};

export const storageReducer = (
  state = initialState,
  action: any
): StorageState => {
  const { type, payload } = action;

  switch (type) {
    case EVENTS.STORAGE_UPDATED:
      return { ...state, storage: payload.storage };

    default:
      return state;
  }
};
