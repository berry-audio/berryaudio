import { useSocketRequest } from "@/store/useSocketRequest";

export const useStorageService = () => {
  const { request } = useSocketRequest();

  return {
    getStorage: (uri?: string) => request("storage.list", {uri}),
    getDir: (path: string) => request("storage.dir", {path}),
    setMount: (dev: string) => request("storage.mount", {dev}),
    setUnMount: (dev: string) => request("storage.unmount", {dev})
  }
};
