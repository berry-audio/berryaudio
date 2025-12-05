import { useSocketRequest } from "@/store/useSocketRequest";

export const useNetworkService = () => {
  const { request } = useSocketRequest();

  return {
    onWifi: (rescan?: boolean) => request("network.wifi", { rescan }),
    getDevices: () => request("network.devices"),
    getDevice: (ifname: string) => request("network.device", { ifname }),
    onConnectWlan: (ssid: string, password: string) => request("network.connect_wlan", { ssid, password }),
    onDelete: (name: string) => request("network.delete", { name }),
    onDisconnect: (ifname: string) => request("network.disconnect", { ifname }),
  };
};
