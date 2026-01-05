import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useBluetoothService } from "@/services/bluetooth";
import { INFO_EVENTS } from "@/store/constants";

export function useBluetoothActions() {
  const dispatch = useDispatch();

  const { devices } = useSelector((state: any) => state.bluetooth);
  const { getDevices } = useBluetoothService();

  const [loading, setLoading] = useState<boolean>(false);

  const fetchDevices = async (rescan: boolean = false) => {
    if (!rescan && devices?.length) return;

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
