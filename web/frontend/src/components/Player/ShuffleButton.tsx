import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { useTracklistService } from "@/services/tracklist";
import { ShuffleIcon } from "@phosphor-icons/react";
import { SHUFFLE_MODE } from "@/constants/states";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";
/**
 * @description 
 * `ShuffleButton` allows users to toggle shuffle mode (on/off).
 * - Syncs with backend and responds to relevant WebSocket events.
 * - Highlights icon when shuffle is active.
 */
const ShuffleButton = () => {
  const { source, shuffle_mode } = useSelector((state: any) => state.player);

  const { setRandom } = useTracklistService();

  const [shuffleMode, setShuffleMode] = useState<SHUFFLE_MODE>(
    SHUFFLE_MODE.SHUFFLE_OFF
  );

  useEffect(() => {
    setShuffleMode(shuffle_mode);
  }, [shuffle_mode]);


  /**
   * Toggles shuffle mode between on and off.
   */
  const onClickShuffle = async () => {
    try {
      const nextMode =
        shuffleMode === SHUFFLE_MODE.SHUFFLE_OFF
          ? SHUFFLE_MODE.SHUFFLE_ON
          : SHUFFLE_MODE.SHUFFLE_OFF;

      await setRandom(nextMode === SHUFFLE_MODE.SHUFFLE_ON);
      setShuffleMode(nextMode);
    } catch (error) {
      console.error("Failed to toggle shuffle mode:", error);
    }
  };

  /**
   * Renders shuffle icon with active/inactive style.
   */
  const RenderShuffle = () => {
    const iconClass =
      shuffleMode === SHUFFLE_MODE.SHUFFLE_OFF
        ? ""
        : "text-primary";

    return (
      <span className={iconClass}>
        <ShuffleIcon weight={ICON_WEIGHT} size={ICON_SM}/>
      </span>
    );
  };

  return (
    <ButtonIcon
      className="w-12 h-12"
      onClick={onClickShuffle}
      disabled={!source.controls?.includes("shuffle")}
    >
      <RenderShuffle/>
    </ButtonIcon>
  );
};

export default ShuffleButton;
