import { EVENTS } from "@/constants/events";
import { DIALOG_EVENTS } from "../constants";

interface DialogState {
  dialog: string | null;
  payload: any;
}

const initialDialogState: DialogState = {
  dialog: null,
  payload: null,
};

export const dialogReducer = (
  state = initialDialogState,
  action: any
): DialogState => {
  const { type, payload } = action;

  switch (type) {
    case DIALOG_EVENTS.DIALOG_PLAYLISTS:
    case DIALOG_EVENTS.DIALOG_PLAYLIST_RENAME:
    case DIALOG_EVENTS.DIALOG_PLAYLIST_DELETE:
    case DIALOG_EVENTS.DIALOG_CLEAR_LIBRARY:
    case DIALOG_EVENTS.DIALOG_ADD_LIBRARY:
    case DIALOG_EVENTS.DIALOG_SCAN_LIBRARY:
    case DIALOG_EVENTS.DIALOG_SCAN_LIBRARY_ARTIST:
    case DIALOG_EVENTS.DIALOG_INFO_LIBRARY:
    case DIALOG_EVENTS.DIALOG_BLUETOOTH_NOT_CONNECTED:
    case DIALOG_EVENTS.DIALOG_WIFI_CONNECT:
    case DIALOG_EVENTS.DIALOG_REBOOT:
    case DIALOG_EVENTS.DIALOG_POWER_OPTIONS:
    case DIALOG_EVENTS.DIALOG_ERROR:
      return {
        dialog: type,
        payload,
      };
    case "dialog/close":
      return {
        dialog: null,
        payload: null,
      };

    default:
      return state;
  }
};
