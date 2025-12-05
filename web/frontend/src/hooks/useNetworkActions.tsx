import { useDispatch } from "react-redux";
import { DIALOG_EVENTS, INFO_EVENTS } from "@/store/constants";
import { useNetworkService } from "@/services/network";
import { WifiNetwork } from "@/types";
import { useState } from "react";
import { EVENTS } from "@/constants/events";

export function useNetworkActions() {
  const dispatch = useDispatch();

  const { onConnectWlan, onDisconnect, onDelete, getDevice, onWifi } = useNetworkService();

  const [loading, setLoading] = useState<boolean>(false);

  const fetchDevices = async () => {
    const wlanDevice = await getDevice("wlan0");
    const ethDevice = await getDevice("eth0");
    const wlanNetworks = await onWifi();

    dispatch({
      type: INFO_EVENTS.WLAN_SCAN_COMPLETED,
      payload: wlanNetworks,
    });

    dispatch({
      type: EVENTS.NETWORK_STATE_CHANGED,
      payload: { state: wlanDevice },
    });

    dispatch({
      type: EVENTS.NETWORK_STATE_CHANGED,
      payload: { state: ethDevice },
    });
  };

  const handleConnectAuth = async (ssid: string, password: string) => {
    setLoading(true);
    await onConnectWlan(ssid, password);
    setLoading(false);
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
  };

  const handleConnectWifi = async (network: WifiNetwork) => {
    if (network.security === "") {
      await handleConnectAuth(network.ssid, "");
    } else {
      dispatch({
        type: DIALOG_EVENTS.DIALOG_WIFI_CONNECT,
        payload: network,
      });
    }
  };

  const handleDisconnect = async (ifname: string) => {
    await onDisconnect(ifname);
  };

  const handleDelete = async (name: string) => {
    await onDelete(name);
  };

  return { fetchDevices, handleConnectWifi, handleConnectAuth, handleDisconnect, handleDelete, loading };
}
