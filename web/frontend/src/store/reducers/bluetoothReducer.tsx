import { BluetoothDevice, BluetoothState } from "@/types";
import { INFO_EVENTS } from "../constants";
import { EVENTS } from "@/constants/events";

const initialState: BluetoothState = {
  adapter_state: { powered: false, discoverable: false, pairable: false, connected: false },
  device_connected: undefined,
  devices_available: [],
};

export const bluetoothReducer = (
  state = initialState,
  action: any
): BluetoothState => {
  const { type, payload } = action;

  switch (type) {
    case INFO_EVENTS.SCAN_BLUETOOTH_COMPLETED:
      return {
        ...state,
        devices_available: payload.sort(
          (a: BluetoothDevice, b: BluetoothDevice) =>
            a.name.localeCompare(b.name)
        ),
      };
    case INFO_EVENTS.SET_BLUETOOTH_STATE:
      return { ...state, adapter_state: payload };
    case EVENTS.BLUETOOTH_STATE_CHANGED:
       return { ...state, adapter_state: payload.state }; 
    case EVENTS.BLUETOOTH_CONNECTED:
    case EVENTS.BLUETOOTH_DISCONNECTED:
      const filter_devices = state.devices_available.filter(
        (device) => device.path !== payload.device.path
      );
      return {
        ...state,
        devices_available: [...filter_devices, { ...payload.device }].sort(
          (a: BluetoothDevice, b: BluetoothDevice) =>
            a.name.localeCompare(b.name)
        ),
      };
    case EVENTS.BLUETOOTH_REMOVED:
        const filter_removed_devices = state.devices_available.filter(
        (device) => device.path !== payload.device.path
      );
      return {
        ...state,
        devices_available: [...filter_removed_devices].sort(
          (a: BluetoothDevice, b: BluetoothDevice) =>
            a.name.localeCompare(b.name)
        ),
      };
    default:
      return state;
  }
};
