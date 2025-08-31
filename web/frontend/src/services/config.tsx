import { useSocketRequest } from "@/store/useSocketRequest";

export const useConfigService = () => {
  const { request } = useSocketRequest();

  return {
    setConfig: (config: {}) => request("config.set", { config }),
    getConfig: () => request("config.get"),
  };
};
