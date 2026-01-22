import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { PowerIcon } from "@phosphor-icons/react";
import { useSystemService } from "@/services/system";

import ButtonIcon from "./ButtonIcon";

const ButtonWake = () => {
  const { setStandby } = useSystemService();

  return (
      <ButtonIcon onClick={async () => await setStandby(false)}>
        <PowerIcon weight={ICON_WEIGHT} size={ICON_SM} className="text-white" />
      </ButtonIcon>
  );
};

export default ButtonWake;
