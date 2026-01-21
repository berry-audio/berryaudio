import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { usePlaybackService } from "@/services/playback";
import { usePlayerActions } from "@/hooks/usePlayerActions";
import { getArtists, getImage, getSourceName } from "@/util";
import { PLAYBACK_STATE } from "@/constants/states";
import { REF } from "@/constants/refs";
import { PLAYER_EVENTS } from "@/store/constants";

import VolumeSlider from "./VolumeSlider";
import PositionSlider from "./PositionSlider";
import RepeatButton from "./RepeatButton";
import ScrollingText from "../ScrollingText";
import ShuffleButton from "./ShuffleButton";
import NextButton from "./NextButton";
import PreviousButton from "./PreviousButton";
import PlayPauseButton from "./PlayPauseButton";
import Directory from "../ListItem/directory";
import ButtonQueue from "../Button/ButtonQueue";
import Source from "../Source";

const Player = () => {
  const dispatch = useDispatch();

  const { getCurrentTrackPos } = usePlaybackService();
  const { openNowPlayingOverlay } = usePlayerActions()

  const { source } = useSelector((state: any) => state.player);
  const { current_track, playback_state } = useSelector((state: any) => state.player);
  const image = getImage(current_track?.track.images?.[0]?.uri);

  const fetch_pos = async () => {
    const elapsed_ms = await getCurrentTrackPos();
    dispatch({
      type: PLAYER_EVENTS.POSITION_UPDATED,
      payload: elapsed_ms,
    });
  };

  useEffect(() => {
    let sync_pos: ReturnType<typeof setInterval> | null = null;
    if (playback_state === PLAYBACK_STATE.PLAYING) {
      fetch_pos();
      sync_pos = setInterval(() => fetch_pos(), 10000);
    }
    return () => {
      if (sync_pos) clearInterval(sync_pos);
    };
  }, [playback_state]);

  return (
    <>
      <div className="z-5 bg-neutral-900 dark:bg-neutral-950 text-white">
        <div className="seek-slider seek-slider-mini h-1 overflow-hidden">
          <PositionSlider/>
        </div>
        <div className="lg:flex hidden px-4 py-2 items-center ">
          <div className="w-3/8">
            <button
              onClick={openNowPlayingOverlay}
              className="flex items-center cursor-pointer w-full  text-left"
            >
              <div className="flex items-center grow">
                <div className="overflow-hidden flex-none rounded-sm mr-3 grayscale-25 w-[50px]  min-w-[50px]">
                  {image ? (
                    <img src={image} alt={current_track?.track.album?.name} className={"object-cover aspect-square w-full"} />
                  ) : (
                    <Directory type={REF.ALBUM} variant="primary"/>
                  )}
                </div>
                {source.type && (
                  <div className="overflow-hidden max-w-80">
                    <h2 className="text-xl tracking-tight ">
                      {current_track?.track.name ? <ScrollingText text={current_track?.track.name} /> : getSourceName(source.type)}
                    </h2>
                    <div className="text-secondary overflow-hidden">
                      {current_track?.track.artists.length ? (
                        <ScrollingText
                          text={`${getArtists(current_track?.track.artists)} ${
                            current_track?.track.album?.name ? " · " + current_track?.track.album?.name : ""
                          }`}
                        />
                      ) : (
                        <Source hideIcon={true} />
                      )}
                    </div>
                  </div>
                )}
              </div>
            </button>
          </div>

          <div className="w-2/8 flex items-center justify-center">
            <ShuffleButton />
            <PreviousButton />
            <PlayPauseButton />
            <NextButton />
            <RepeatButton />
          </div>

          <div className="w-3/8 text-right">
            <div className="flex justify-end text-right items-center">
              <div className="flex items-center gap-3 w-50 max-w-xs mr-5">
                <VolumeSlider classname="volume-slider " />
              </div>
              <div className="flex items-center">
                <div className="mr-2"></div>
                <ButtonQueue />
              </div>
            </div>
          </div>
        </div>

        {/* Mini Player  */}
        <div className="lg:hidden flex items-center justify-between relative bg-neutral-950 text-white">
          <div className="flex items-center p-2 w-4/6 z-20 relative">
            <button onClick={openNowPlayingOverlay} className="w-full cursor-pointer text-left">
              <div className="flex items-center">
                <div className={`overflow-hidden rounded-sm mr-3 min-w-10 w-10 grayscale-25`}>
                  {image ? (
                    <img src={image} alt={current_track?.track.album?.name} className={`object-cover aspect-square w-full`} />
                  ) : (
                    <Directory type={REF.ALBUM} variant="primary"/>
                  )}
                </div>
                {source.type && (
                  <div className="text-left overflow-hidden">
                    <h2 className={`text-lg font-medium tracking-tight text-white`}>
                      {current_track?.track.name ? <ScrollingText text={current_track?.track.name} /> : getSourceName(source.type)}
                    </h2>
                    <div className=" text-secondary -mt-0.5 lg:-mt-1 text-sm">
                      {current_track?.track.artists.length ? (
                        <ScrollingText
                          text={`${getArtists(current_track?.track.artists)} ${
                            current_track?.track.album?.name ? " · " + current_track?.track.album?.name : ""
                          }`}
                        />
                      ) : (
                        <Source hideIcon={true} />
                      )}
                    </div>
                  </div>
                )}
              </div>
            </button>
          </div>

          <div className="flex items-center w-2/6 justify-end z-20 relative text-white">
            <div className="mr-2"></div>
            <PlayPauseButton />
          </div>
        </div>
      </div>
    </>
  );
};

export default React.memo(Player);
