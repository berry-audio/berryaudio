import { useSelector } from "react-redux";
import { useBluetoothActions } from "@/hooks/useBluetoothActions";
import { ArrowsClockwiseIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";
import Spinner from "@/components/Spinner";

const ButtonBluetoothScan = () => {
  const { adapter_state } = useSelector((state: any) => state.bluetooth);
  const { fetchDevices, loading } = useBluetoothActions();

  return (
    <ButtonIcon onClick={() => fetchDevices(true)} className="mr-1" disabled={!adapter_state?.powered}>
      {loading ? <Spinner /> : <ArrowsClockwiseIcon weight={ICON_WEIGHT} size={ICON_SM} />}
    </ButtonIcon>
  );
};

export default ButtonBluetoothScan;
