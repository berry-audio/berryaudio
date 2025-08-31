import { useSocketRequest } from "@/store/useSocketRequest";

export const useSystemService = () => {
  const { request } = useSocketRequest();

  return {
    getSystemInfo: () => request("system.info"),
    getSystemTime: () => request("system.datetime"),
    setReboot: () => request("system.reboot"),
    setShutdown: () => request("system.shutdown"),
    getPowerState: () => request("system.get_power_state"),
    setStandby: (state:boolean) => request("system.standby", {state}),
  };
};
