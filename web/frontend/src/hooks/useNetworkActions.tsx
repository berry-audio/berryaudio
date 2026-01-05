import { useDispatch, useSelector } from "react-redux";
import { DIALOG_EVENTS, INFO_EVENTS } from "@/store/constants";
import { useNetworkService } from "@/services/network";
import { WifiNetwork } from "@/types";
import { useState } from "react";
import { EVENTS } from "@/constants/events";

export function useNetworkActions() {
  const dispatch = useDispatch();
  const { devices, networks } = useSelector((state: any) => state.network);

  const { onConnectWlan, onDisconnect, onDelete, getDevice, onModify, getConnection, onWifi } = useNetworkService();

  const [loading, setLoading] = useState<boolean>(false);

  const fetchDevices = async () => {
    if (Object.keys(devices).length) {
      setLoading(true);
      Object.keys(devices).map(async (ifname) => {
        const device = await getDevice(ifname);

        dispatch({
          type: EVENTS.NETWORK_STATE_CHANGED,
          payload: { device },
        });
      });
      setLoading(false);
    }
  };

  const fetchWifiNetworks = async (rescan: boolean = false) => {
    if (!rescan && networks?.length) return;

    setLoading(true);
    const networks_discovered = await onWifi(rescan);

    dispatch({
      type: INFO_EVENTS.WLAN_SCAN_COMPLETED,
      payload: networks_discovered,
    });
    setLoading(false);
  };

  const modifyNetwork = async (ifname: string, name: string, ipv4_address: string, ipv4_gateway: string, ipv4_dns: string, method: string) => {
    setLoading(true);
    await onModify(ifname, name, ipv4_address, ipv4_gateway, ipv4_dns, method);
    setLoading(false);
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
  };

  const handleModifyNetwork = async (connection: string) => {
    const device = await getConnection(connection);
    if (!device?.name) return;

    dispatch({
      type: DIALOG_EVENTS.DIALOG_EDIT_NETWORK,
      payload: device,
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
        type: DIALOG_EVENTS.DIALOG_WIFI_AUTH,
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

  return {
    fetchWifiNetworks,
    fetchDevices,
    modifyNetwork,
    handleConnectWifi,
    handleConnectAuth,
    handleDisconnect,
    handleDelete,
    handleModifyNetwork,
    loading,
  };
}
