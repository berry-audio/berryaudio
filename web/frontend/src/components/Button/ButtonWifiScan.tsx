import { useState } from "react";
import { useDispatch } from "react-redux";
import { useNetworkService } from "@/services/network";
import { ArrowsClockwiseIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { INFO_EVENTS } from "@/store/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";
import Spinner from "@/components/Spinner";

const ButtonWifiScan = () => {
  const dispatch = useDispatch();

  const { onWifi } = useNetworkService();

  const [isLoading, setIsLoading] = useState<boolean>(false);

  const startScan = async () => {
    setIsLoading(true);
    const _res = await onWifi(true);
    dispatch({
      type: INFO_EVENTS.WLAN_SCAN_COMPLETED,
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
