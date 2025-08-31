import { useSocketRequest } from "@/store/useSocketRequest";

export const useSearchService = () => {
  const { request } = useSocketRequest();

  return {
    getSearch: (query?: string) => request("search.search", {query}),
  }
};
