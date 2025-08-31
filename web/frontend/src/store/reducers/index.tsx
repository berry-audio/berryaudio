import { combineReducers } from "redux";
import { socketReducer } from "./socketReducer";
import { dialogReducer } from "./dialogReducer";
import { eventReducer } from "./eventReducer";
import { playerReducer } from "./playerReducer";
import { systemReducer } from "./systemReducer";
import { overlayReducer } from "./overlayReducer";
import { storageReducer } from "./storageReducer";
import { bluetoothReducer } from "./bluetoothReducer";
import { scanReducer } from "./scanReducer";

export const rootReducer = combineReducers({
  socket: socketReducer,
  event: eventReducer,
  dialog: dialogReducer,
  overlay: overlayReducer,
  player: playerReducer,
  system: systemReducer,
  storage: storageReducer,
  scan: scanReducer,
  bluetooth: bluetoothReducer,
});
