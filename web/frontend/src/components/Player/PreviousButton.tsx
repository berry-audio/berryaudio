import { SkipBackIcon } from "@phosphor-icons/react";
import { useSelector } from "react-redux";
import { usePlaybackService } from "@/services/playback";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";

/**
 * @description
 * `PreviousButton` component that skips to the prev track in the playback queue.
 * - Calls the `prev()` method from the playback service.
 */
const PreviousButton = () => {
  const { source } = useSelector((state: any) => state.player);
  const { prev } = usePlaybackService();

  /**
   * Triggers playback to skip to the next track.
   */
  const onClickPrev = async () => {
    try {
      await prev();
    } catch (error) {
      console.error("Failed to skip to prev track:", error);
    }
  };

  return (
    <ButtonIcon
      className="w-12 h-12"
      onClick={onClickPrev}
      disabled={!source.controls?.includes("previous")}
    >
      <SkipBackIcon size={ICON_SM + 6} weight={ICON_WEIGHT} />
    </ButtonIcon>
  );
};

export default PreviousButton;
