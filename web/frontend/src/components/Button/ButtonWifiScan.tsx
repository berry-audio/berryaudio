import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNetworkService } from "@/services/network";
import { ArrowsClockwiseIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { INFO_EVENTS } from "@/store/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";
import Spinner from "@/components/Spinner";

const ButtonWifiScan = () => {
  const dispatch = useDispatch();
  const { adapter_state } = useSelector((state: any) => state.bluetooth);
  const { scanNetwork } = useNetworkService();

  const [isLoading, setIsLoading] = useState<boolean>(false);

  const startScan = async () => {
    setIsLoading(true);
    const _res = await scanNetwork();
    dispatch({
      type: INFO_EVENTS.SCAN_WIFI_COMPLETED,
      payload: _res,
    });
    setIsLoading(false);
  };

  return (
    <ButtonIcon onClick={() => startScan()} className="mr-1">
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

export default ButtonWifiScan;
