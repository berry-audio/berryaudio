import { useSocketRequest } from "@/store/useSocketRequest";

export const useNetworkService = () => {
  const { request } = useSocketRequest();

  return {
    scanNetwork : () => request("network.scan"),
    getDevices: () => request("network.devices"),
    getDevice: (ifname: string) => request("network.device", { ifname })
  }
};
