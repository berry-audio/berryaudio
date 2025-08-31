import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { usePlaybackService } from "@/services/playback";
import { Slider } from "@/components/Form/Slider";
import { getPosition, getTotalDuration } from "@/util";
import { PLAYBACK_STATE } from "@/constants/states";

import StreamInfo from "./StreamInfo";

/**
 * @description
 * `PositionSlider` is a UI component that reflects and controls the playback position of the current track.
 * It synchronizes with backend playback state and updates in real time while playing.
 * Users can also manually seek within the track using this slider.
 */
const PositionSlider = ({
  className,
  showElapsedNumber = false,
}: {
  className?: string;
  showElapsedNumber?: boolean;
}) => {
  const { elapsed_ms, playback_state, current_track } = useSelector((state: any) => state.player);
  const { setSeek } = usePlaybackService();

  const [plTrackPos, setPlTrackPos] = useState<number>(elapsed_ms);
  const [plSliderPos, setPlSliderPos] = useState<number>(elapsed_ms);

  useEffect(() => {
    let ticker: ReturnType<typeof setInterval> | null = null;
    if (playback_state === PLAYBACK_STATE.PLAYING) {
      ticker = setInterval(() => setPlSliderPos((prev) => prev + 1000), 1000);     
    } else if (playback_state === PLAYBACK_STATE.STOPPED) {
      setPlSliderPos(0);
    }
    return () => {
      if (ticker) clearInterval(ticker);
    };
  }, [playback_state]);

  useEffect(() => {
    setPlSliderPos(plTrackPos);
  }, [plTrackPos]);


   useEffect(() => {
    setPlSliderPos(elapsed_ms);
  }, [elapsed_ms]);

  /**
   * Updates track position locally and on the backend.
   * @param position - The position in milliseconds to seek to
   */
  const setPosition = async (position: number) => {
    try {
      setPlTrackPos(position);
      await setSeek(position);
    } catch (error) {
      console.error("Failed to set seek position:", error);
    }
  };

  return (
    <>
      <Slider
        value={[plSliderPos]}
        max={current_track?.track.length || 100}
        disabled={!current_track?.track.length}
        onValueChange={([value]) => setPlSliderPos(value)}
        onValueCommit={([value]) => setPosition(value)}
        className={className}
      />
      {showElapsedNumber && (
        <div className="flex mt-4 items-center">
          <div className="text-left w-2/12">{getPosition(plSliderPos)}</div>
          <div className="opacity-50 text-center w-8/12">
            <StreamInfo />
          </div>
          <div className="text-right w-2/12">
              {getTotalDuration(current_track?.track.length)}
          </div>
        </div>
      )}
    </>
  );
};

export default React.memo(PositionSlider);
