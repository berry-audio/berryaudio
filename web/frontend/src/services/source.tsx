import { useSocketRequest } from "@/store/useSocketRequest";

export const useSourceService = () => {
    const { request } = useSocketRequest();

    return {
      getSource: () => request("source.get"),
      setSource: (type: string) => request("source.set", {type}),
    };
  };
