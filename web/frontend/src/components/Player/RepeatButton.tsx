import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { useTracklistService } from "@/services/tracklist";
import { REPEAT_MODE } from "@/constants/states";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { RepeatOnceIcon, RepeatIcon } from "@phosphor-icons/react";

import ButtonIcon from "@/components/Button/ButtonIcon";

/**
 * @description
 * `RepeatButton` is a playback control that cycles through repeat modes:
 * - Off → Repeat One → Repeat All → Off
 * Syncs state from backend and updates via WebSocket events.
 */
const RepeatButton = () => {
  const { source, repeat_mode } = useSelector((state: any) => state.player);
  const { setRepeat, setSingle } = useTracklistService();
  
  const [repeatMode, setRepeatMode] = useState(REPEAT_MODE.REPEAT_OFF);

  useEffect(() => {
    setRepeatMode(repeat_mode);
  }, [repeat_mode]);

  /**
   * Handles repeat mode cycling in order: Off → Single → All → Off
   */
  const onClickRepeat = async () => {
    try {
      switch (repeatMode) {
        case REPEAT_MODE.REPEAT_OFF:
          await setRepeat(true);
          await setSingle(true);
          setRepeatMode(REPEAT_MODE.REPEAT_SINGLE);
          break;
        case REPEAT_MODE.REPEAT_SINGLE:
          await setRepeat(true);
          await setSingle(false);
          setRepeatMode(REPEAT_MODE.REPEAT_ALL);
          break;
        case REPEAT_MODE.REPEAT_ALL:
        default:
          await setRepeat(false);
          await setSingle(false);
          setRepeatMode(REPEAT_MODE.REPEAT_OFF);
          break;
      }
    } catch (error) {
      console.error("Failed to toggle repeat mode:", error);
    }
  };

  /**
   * Renders appropriate icon based on current repeat mode.
   */
  const RenderRepeat = () => {
    const iconClass =
      repeatMode === REPEAT_MODE.REPEAT_OFF ? "" : "text-primary";

    return (
      <span className={iconClass}>
        {repeatMode === REPEAT_MODE.REPEAT_SINGLE ? (
          <RepeatOnceIcon weight={ICON_WEIGHT} size={ICON_SM} />
        ) : (
          <RepeatIcon weight={ICON_WEIGHT} size={ICON_SM} />
        )}
      </span>
    );
  };

  return (
    <ButtonIcon
      className="w-12 h-12"
      onClick={onClickRepeat}
      disabled={!source.controls?.includes("repeat")}
    >
      <RenderRepeat />
    </ButtonIcon>
  );
};

export default RepeatButton;
