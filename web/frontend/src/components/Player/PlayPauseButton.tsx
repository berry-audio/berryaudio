import { PauseIcon, PlayIcon } from "@phosphor-icons/react";
import { useSelector } from "react-redux";
import { usePlaybackService } from "@/services/playback";
import { PLAYBACK_STATE } from "@/constants/states";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";

/**
 * @description
 * `PlayPauseButton` component that controls the playback state.
 * - Calls the `play()` or `pause()` method from the playback service.
 */
const PlayPauseButton = () => {
  const { source, playback_state } = useSelector((state: any) => state.player);
  const { play, pause } = usePlaybackService();

  const onClickPlayPause = async () => {
    if (playback_state === PLAYBACK_STATE.PLAYING) {
      await pause();
    } else {
      await play();
    }
  };

  return (
    <ButtonIcon
      className="w-16 h-16 bg-black"
      onClick={onClickPlayPause}
      disabled={!source?.controls?.includes("play")}
    >
      {playback_state === PLAYBACK_STATE.PLAYING ? (
        <PauseIcon size={ICON_SM + 7} weight={ICON_WEIGHT} className="text-white"/>
      ) : (
         <PlayIcon size={ICON_SM + 7} weight={ICON_WEIGHT} className="text-white"/>
      )}
    </ButtonIcon>
  );
};

export default PlayPauseButton;
