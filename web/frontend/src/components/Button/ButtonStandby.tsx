import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { PowerIcon } from "@phosphor-icons/react";
import { DIALOG_EVENTS } from "@/store/constants";
import { useDispatch } from "react-redux";

import ButtonIcon from "./ButtonIcon";

const ButtonStandby = () => {
  const dispatch = useDispatch();

  return (
    <ButtonIcon
      onClick={() => dispatch({ type: DIALOG_EVENTS.DIALOG_POWER_OPTIONS })}
    >
      <PowerIcon
        weight={ICON_WEIGHT}
        size={ICON_SM}
        className="dark:text-white text-neutral-950"
      />
    </ButtonIcon>
  );
};

export default ButtonStandby;
