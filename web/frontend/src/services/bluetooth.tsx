import { useSocketRequest } from "@/store/useSocketRequest";

export const useBluetoothService = () => {
  const { request } = useSocketRequest();

  return {
    getDevices: (rescan: boolean) => request("bluetooth.devices", { rescan }),
    getAdapterState: () => request("bluetooth.adapter_get_state"),
    setAdapterState: (state: boolean) => request("bluetooth.adapter_set_state", { state }),
    removeDevice: (path: string) => request("bluetooth.remove", { path }),
    disconnectDevice: (path: string) => request("bluetooth.disconnect", { path }),
    connectDevice: (path: string) => request("bluetooth.connect", { path })
  }
};
