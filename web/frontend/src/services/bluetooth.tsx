import { useSocketRequest } from "@/store/useSocketRequest";

export const useBluetoothService = () => {
  const { request } = useSocketRequest();

  return {
    getDevices: (rescan: boolean) => request("bluetooth.devices", { rescan }),
    getAdapterState: () => request("bluetooth.adapter_get_state"),
    setAdapterState: (state: boolean) => request("bluetooth.adapter_set_state", { state }),
    removeDevice: (address: string) => request("bluetooth.remove", { address }),
    disconnectDevice: (address: string) => request("bluetooth.disconnect", { address }),
    connectDevice: (address: string) => request("bluetooth.connect", { address })
  }
};
