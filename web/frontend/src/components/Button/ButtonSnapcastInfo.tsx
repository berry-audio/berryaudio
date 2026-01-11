import { useSnapcastActions } from "@/hooks/useSnapcastActions";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { InfoIcon } from "@phosphor-icons/react";

import ButtonIcon from "@/components/Button/ButtonIcon";

const ButtonSnapcastInfo = () => {
  const { showServerInfo } = useSnapcastActions();

  return (
    <ButtonIcon onClick={() => showServerInfo()}>
      <InfoIcon weight={ICON_WEIGHT} size={ICON_SM} />
    </ButtonIcon>
  );
};

export default ButtonSnapcastInfo;
