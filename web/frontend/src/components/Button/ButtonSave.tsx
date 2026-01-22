import { ArrowsClockwiseIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "./ButtonIcon";
import Spinner from "../Spinner";

const ButtonSave = ({ onClick, isLoading, disabled }: { onClick: () => void; isLoading?: boolean; disabled?: boolean }) => {
  return (
    <ButtonIcon onClick={onClick} className="mr-1" disabled={disabled}>
      {isLoading ? <Spinner /> : <ArrowsClockwiseIcon weight={ICON_WEIGHT} size={ICON_SM} />}
    </ButtonIcon>
  );
};

export default ButtonSave;
