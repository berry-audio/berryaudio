import { useDispatch } from "react-redux";
import { UserSwitchIcon } from "@phosphor-icons/react";
import { DIALOG_EVENTS } from "@/store/constants";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";

/**
 * A button component that scans the library artist
 *
 * @returns {JSX.Element} The rendered clear playlist button.
 */
const ButtonScanArtist = ({ disabled }: { disabled?: boolean }) => {
  const dispatch = useDispatch();

  return (
    <ButtonIcon onClick={() => dispatch({ type: DIALOG_EVENTS.DIALOG_SCAN_LIBRARY_ARTIST })} disabled={disabled}>
      <UserSwitchIcon weight={ICON_WEIGHT} size={ICON_SM} />
    </ButtonIcon>
  );
};

export default ButtonScanArtist;
