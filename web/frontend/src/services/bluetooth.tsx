import { useSocketRequest } from "@/store/useSocketRequest";

export const useBluetoothService = () => {
  const { request } = useSocketRequest();

  return {
    discoverDevices : () => request("bluetooth.discover"),
    getDevices: () => request("bluetooth.devices"),
    getAdapterState: () => request("bluetooth.adapter_get_state"),
    setAdapterState: (state: boolean) => request("bluetooth.adapter_set_state", { state }),
    removeDevice: (path: string) => request("bluetooth.remove", { path }),
    disconnectDevice: (path: string) => request("bluetooth.disconnect", { path }),
    connectDevice: (path: string) => request("bluetooth.connect", { path })
  }
};
