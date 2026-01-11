import { useDispatch } from "react-redux";
import { ArrowsClockwiseIcon } from "@phosphor-icons/react";
import { DIALOG_EVENTS } from "@/store/constants";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";

/**
 * A button component that scans the library
 *
 * @returns {JSX.Element} The rendered clear playlist button.
 */
const ButtonScanLibrary = ({ disabled }: { disabled?: boolean }) => {
  const dispatch = useDispatch();

  return (
    <ButtonIcon onClick={() => dispatch({ type: DIALOG_EVENTS.DIALOG_SCAN_LIBRARY })} disabled={disabled}>
      <ArrowsClockwiseIcon weight={ICON_WEIGHT} size={ICON_SM} />
    </ButtonIcon>
  );
};

export default ButtonScanLibrary;
