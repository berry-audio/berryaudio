import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { useTracklistService } from "@/services/tracklist";
import { TrashSimpleIcon } from "@phosphor-icons/react";

import ButtonIcon from "@/components/Button/ButtonIcon";

/**
 * A button component that clears the current queue.
 *
 * @returns {JSX.Element} The rendered clear playlist button.
 */
const ButtonQueueClear = () => {
  const { clear } = useTracklistService();

  return (
    <ButtonIcon onClick={()=>clear()}>
      <TrashSimpleIcon weight={ICON_WEIGHT} size={ICON_SM} />
    </ButtonIcon>
  );
};

export default ButtonQueueClear;
