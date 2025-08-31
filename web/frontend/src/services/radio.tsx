import { useSocketRequest } from "@/store/useSocketRequest";

export const useRadioService = () => {
  const { request } = useSocketRequest();

  return {
    getDirectory: (uri?: string, limit?: number, offset?:number) => request("radio.directory", {uri, limit, offset}),
    search: (value: string) =>
      request("radio.search", { query: { any: [value] } }),
  };
};
