import { useState } from "react";
import { useDispatch } from "react-redux";
import { useSnapcastService } from "@/services/snapcast";
import { DIALOG_EVENTS, INFO_EVENTS } from "@/store/constants";
import { EVENTS } from "@/constants/events";

export function useSnapcastActions() {
  const dispatch = useDispatch();
  const { getServers, getStatus } = useSnapcastService();

  const [loading, setLoading] = useState<boolean>(false);

  const fetchServers = async (rescan: boolean = false) => {
    setLoading(true);
    const response = await getServers(rescan);

    dispatch({
      type: INFO_EVENTS.SNAPCAST_SCAN_COMPLETED,
      payload: response,
    });

    getServerStatus();
    setLoading(false);
  };

  const getServerStatus = async () => {
    setLoading(true);
    const response = await getStatus();

    dispatch({
      type: EVENTS.SNAPCAST_STATE_CHANGED,
      payload: response,
    });
    setLoading(false);
  };

  const showServerInfo = () => {
    dispatch({ type: DIALOG_EVENTS.DIALOG_SNAPCAST_INFO });
  };

  return {
    fetchServers,
    getServerStatus,
    showServerInfo,
    loading,
  };
}
