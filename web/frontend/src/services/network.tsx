import { useSocketRequest } from "@/store/useSocketRequest";

export const useNetworkService = () => {
  const { request } = useSocketRequest();

  return {
    onWifi: (rescan?: boolean) => request("network.wifi", { rescan }),
    getDevices: () => request("network.devices"),
    getDevice: (ifname: string) => request("network.device", { ifname }),
    getConnection: (name: string) => request("network.connection", { name }),
    onConnectWlan: (ssid: string, password: string) => request("network.connect_wlan", { ssid, password }),
    onDelete: (name: string) => request("network.delete", { name }),
    onDisconnect: (ifname: string) => request("network.disconnect", { ifname }),
    onModify: (ifname: string, name: string, ipv4_address: string, ipv4_gateway: string, ipv4_dns: string, method: string) =>
      request("network.modify", { ifname, name, ipv4_address, ipv4_gateway, ipv4_dns, method }),
  };
};
