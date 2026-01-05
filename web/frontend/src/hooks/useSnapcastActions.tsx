import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSnapcastService } from "@/services/snapcast";
import { INFO_EVENTS } from "@/store/constants";

export function useSnapcastActions() {
  const dispatch = useDispatch();
  const connected = useSelector((state: any) => state.socket.connected);
  const { servers } = useSelector((state: any) => state.snapcast);
  const { getServers } = useSnapcastService();

  const [loading, setLoading] = useState<boolean>(false);

  const fetchServers = async (rescan: boolean = false) => {
    if (!connected) return;
    if (!rescan && servers?.length) return;

    setLoading(true);
    const response = await getServers(rescan);

    dispatch({
      type: INFO_EVENTS.SNAPCAST_SCAN_COMPLETED,
      payload: response,
    });
    setLoading(false);
  };

  return {
    fetchServers,
    loading,
  };
}
