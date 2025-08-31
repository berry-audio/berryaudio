import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useBluetoothService } from "@/services/bluetooth";
import { ArrowsClockwiseIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { INFO_EVENTS } from "@/store/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";
import Spinner from "@/components/Spinner";

const ButtonBluetoothScan = () => {
  const dispatch = useDispatch();
  const { adapter_state } = useSelector((state: any) => state.bluetooth);
  const { discoverDevices } = useBluetoothService();

  const [isLoading, setIsLoading] = useState<boolean>(false);

  const startScan = async () => {
    setIsLoading(true);
    const res = await discoverDevices();
    dispatch({
      type: INFO_EVENTS.SCAN_BLUETOOTH_COMPLETED,
      payload: res,
    });
    setIsLoading(false);
  };

  return (
    <ButtonIcon onClick={() => startScan()} className="mr-1" disabled={!adapter_state.powered}>
      {isLoading ? (
        <Spinner />
      ) : (
        <ArrowsClockwiseIcon
          weight={ICON_WEIGHT}
          size={ICON_SM}
          className="dark:text-white text-black"
        />
      )}
    </ButtonIcon>
  );
};

export default ButtonBluetoothScan;
