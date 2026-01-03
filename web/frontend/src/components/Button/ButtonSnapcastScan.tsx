import { useState } from "react";
import { useDispatch } from "react-redux";
import { useSnapcastService } from "@/services/snapcast";
import { ArrowsClockwiseIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { INFO_EVENTS } from "@/store/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";
import Spinner from "@/components/Spinner";

const ButtonSnapcastScan = () => {
  const dispatch = useDispatch();
  const { getServers } = useSnapcastService();

  const [isLoading, setIsLoading] = useState<boolean>(false);

  const startScan = async () => {
    setIsLoading(true);
    const res = await getServers(true)
    dispatch({
      type: INFO_EVENTS.SNAPCAST_SCAN_COMPLETED,
      payload: res,
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

export default ButtonSnapcastScan;
