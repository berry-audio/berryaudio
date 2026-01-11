import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { PowerIcon } from "@phosphor-icons/react";
import { useSystemService } from "@/services/system";

import ButtonIcon from "./ButtonIcon";

const ButtonWake = () => {
  const { setStandby } = useSystemService();

  return (
    <div className="dark">
      <ButtonIcon onClick={async () => await setStandby(false)}>
        <PowerIcon weight={ICON_WEIGHT} size={ICON_SM} />
      </ButtonIcon>
    </div>
  );
};

export default ButtonWake;
