import { useDispatch } from "react-redux";
import { DIALOG_EVENTS } from "@/store/constants";
import { useNetworkService } from "@/services/network";
import { WifiNetwork } from "@/types";
import { useState } from "react";
import { EVENTS } from "@/constants/events";

export function useNetworkActions() {
  const dispatch = useDispatch();

  const { onConnectWlan, onDisconnect, onDelete, getDevice, onModify, onWifi, getConnection } = useNetworkService();

  const [loading, setLoading] = useState<boolean>(false);

  const fetchDevices = async (device:string) => {
    const _device = await getDevice(device);
    const _wlanNetworks = await onWifi();

    dispatch({
      type: EVENTS.NETWORK_STATE_CHANGED,
      payload: { device: _device, networks: _wlanNetworks },
    });

  };


  const modifyNetwork = async (ifname: string, name: string, ipv4_address: string, ipv4_gateway: string, ipv4_dns: string, method: string) => {
    setLoading(true);
    await onModify(ifname, name, ipv4_address, ipv4_gateway, ipv4_dns, method);
    setLoading(false);
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
  };

  const handleModifyNetwork = async (name: string) => {
    const device = await getConnection(name);

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
