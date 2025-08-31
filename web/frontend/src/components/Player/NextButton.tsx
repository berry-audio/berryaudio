import { useSelector } from "react-redux";
import { usePlaybackService } from "@/services/playback";
import { SkipForwardIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";

/**
 * @description
 * `NextButton` component that skips to the next track in the playback queue.
 * - Calls the `next()` method from the playback service.
 */
const NextButton = () => {
  const { source } = useSelector((state: any) => state.player);
  const { next } = usePlaybackService();

  /**
   * Triggers playback to skip to the next track.
   */
  const onClickNext = async () => {
    try {
      await next();
    } catch (error) {
      console.error("Failed to skip to next track:", error);
    }
  };

  return (
    <ButtonIcon
      className="w-12 h-12"
      onClick={onClickNext}
      disabled={!source?.controls?.includes("next")}
    > 
    <SkipForwardIcon size={ICON_SM + 6} weight={ICON_WEIGHT}/>
    </ButtonIcon>
  );
};

export default NextButton;
