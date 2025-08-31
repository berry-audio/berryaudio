import { Ref } from "@/types";
import { useNavigate } from "react-router-dom";

export function useGoToArtist() {
  const navigate = useNavigate();

  const handleGoToArtist = (item: Ref) => {
    if (!item?.artists?.length) return;
    const [view, id] = item?.artists[0].uri.split(":");
    navigate(`/library/${view}/${id}`);
  };

  return { handleGoToArtist };
}
