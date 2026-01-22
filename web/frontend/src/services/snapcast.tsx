import { useSocketRequest } from "@/store/useSocketRequest";

export const useSnapcastService = () => {
  const { request } = useSocketRequest();

  return {
    getServers: (rescan?: boolean) => request("snapcast.servers", { rescan }),
    getStatus: () => request("snapcast.get_status"),
    setVolume: (client_id: string, volume: number, mute?: boolean) => request("snapcast.set_volume", { client_id, volume, mute }),
    connect: (ip: string) => request("snapcast.connect", { ip }),
    disconnect: () => request("snapcast.disconnect"),
  };
};
