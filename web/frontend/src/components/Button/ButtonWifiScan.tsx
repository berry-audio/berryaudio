import { useNetworkActions } from "@/hooks/useNetworkActions";
import { ArrowsClockwiseIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";
import Spinner from "@/components/Spinner";

const ButtonWifiScan = () => {
  const { fetchWifiNetworks, loading } = useNetworkActions();

  return (
    <ButtonIcon onClick={() => fetchWifiNetworks(true)} className="mr-1">
      {loading ? <Spinner /> : <ArrowsClockwiseIcon weight={ICON_WEIGHT} size={ICON_SM} className="dark:text-white text-black" />}
    </ButtonIcon>
  );
};

export default ButtonWifiScan;
