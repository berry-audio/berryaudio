import { useSocketRequest } from "@/store/useSocketRequest";

export const useStorageService = () => {
  const { request } = useSocketRequest();

  return {
    getStorage: (uri?: string) => request("storage.directory", {uri}),
    setMount: (dev: string) => request("storage.mount", {dev}),
    setUnMount: (dev: string) => request("storage.unmount", {dev})
  }
};
