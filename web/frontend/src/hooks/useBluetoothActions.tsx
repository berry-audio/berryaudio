import { useState } from "react";
import { useDispatch } from "react-redux";
import { useBluetoothService } from "@/services/bluetooth";
import { INFO_EVENTS } from "@/store/constants";

export function useBluetoothActions() {
  const dispatch = useDispatch();

  const { getDevices } = useBluetoothService();

  const [loading, setLoading] = useState<boolean>(false);

  const fetchDevices = async (rescan: boolean = false) => {
    setLoading(true);
    const response = await getDevices(rescan);

    dispatch({
      type: INFO_EVENTS.BLUETOOTH_SCAN_COMPLETED,
      payload: response,
    });
    setLoading(false);
  };

  return {
    fetchDevices,
    loading,
  };
}
