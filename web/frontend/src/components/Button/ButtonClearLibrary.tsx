import { useDispatch } from "react-redux";
import { TrashIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { DIALOG_EVENTS } from "@/store/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";

const ButtonClearLibrary = () => {
  const dispatch = useDispatch();

  return (
    <ButtonIcon onClick={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLEAR_LIBRARY })}>
      <TrashIcon weight={ICON_WEIGHT} size={ICON_SM} />
    </ButtonIcon>
  );
};

export default ButtonClearLibrary;
