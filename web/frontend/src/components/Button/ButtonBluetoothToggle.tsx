import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useBluetoothService } from "@/services/bluetooth";
import { BluetoothIcon, BluetoothSlashIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { INFO_EVENTS } from "@/store/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";

const ButtonBluetoothToggle = () => {
  const dispatch = useDispatch();

  const { adapter_state } = useSelector((state: any) => state.bluetooth);
  const { getAdapterState, setAdapterState } = useBluetoothService();


  const toggleBluetooth = async () => {
    const res = await setAdapterState(!adapter_state.powered);
    dispatch({
      type: INFO_EVENTS.SET_BLUETOOTH_STATE,
      payload: res,
    });
  };

  const fetchAdapterState = async () => {
    const res = await getAdapterState();
    dispatch({
      type: INFO_EVENTS.SET_BLUETOOTH_STATE,
      payload: res,
    });
  };

  useEffect(() => {
    fetchAdapterState();
  }, []);


  return (
    <ButtonIcon onClick={() => toggleBluetooth()} className="mr-1">
      {adapter_state.powered ? (
        <BluetoothIcon
          weight={ICON_WEIGHT}
          size={ICON_SM}
          className={`${adapter_state.discoverable ? 'text-yellow-700' : 'dark:text-white text-black '}`}
        />
      ) : (
        <BluetoothSlashIcon
          weight={ICON_WEIGHT}
          size={ICON_SM}
          className="dark:text-white text-black"
        />
      )}
    </ButtonIcon>
  );
};

export default ButtonBluetoothToggle;
