import React from "react";
import { CaretDownIcon, UserIcon, VinylRecordIcon } from "@phosphor-icons/react";
import { useDispatch, useSelector } from "react-redux";
import { getAlbums, getArtists, getImage, getSourceName } from "@/util";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { PLAYBACK_STATE } from "@/constants/states";
import { OVERLAY_EVENTS } from "@/store/constants";
import { REF } from "@/constants/refs";
import { Menu } from "../Menu";

import PositionSlider from "../Player/PositionSlider";
import RepeatButton from "../Player/RepeatButton";
import ScrollingText from "../ScrollingText";
import NextButton from "../Player/NextButton";
import PreviousButton from "../Player/PreviousButton";
import PlayPauseButton from "../Player/PlayPauseButton";
import Page from "../Page";
import Source from "../Source";
import FavouriteButton from "../Player/FavouriteButton";
import Overlay from ".";
import ShuffleButton from "../Player/ShuffleButton";
import ButtonIcon from "@/components/Button/ButtonIcon";
import ButtonQueue from "../Button/ButtonQueue";
import Directory from "../ListItem/directory";

const OverlayNowPlaying = () => {
  const dispatch = useDispatch();

  const { overlay } = useSelector((state: any) => state.overlay);
  const { source } = useSelector((state: any) => state.player);

  const { current_track, playback_state } = useSelector((state: any) => state.player);

  const image = getImage(current_track?.track.images?.[0]?.uri);

  const ButtonCollapse = () => {
    return (
      <ButtonIcon className="hover:bg-black opacity-60 z-51 absolute top-12 right-4" onClick={() => dispatch({ type: OVERLAY_EVENTS.OVERLAY_CLOSE })}>
        <CaretDownIcon weight={ICON_WEIGHT} size={ICON_SM} />
      </ButtonIcon>
    );
  };

  return (
    <Overlay show={overlay === OVERLAY_EVENTS.OVERLAY_NOWPLAYING} full className="dark text-white" zindex={30}>
      <div className="bg-background w-full h-full absolute">
        <div
          className="h-full bg-cover blur-3xl opacity-80"
          style={overlay === OVERLAY_EVENTS.OVERLAY_NOWPLAYING ? { backgroundImage: `url(${image})` } : {}}
        ></div>
      </div>
      <Menu />
      <Page>
        {/* Start Vertical Layout */}
        <ButtonCollapse />
        <div className="h-600-hide -mt-[30px] px-6 relative z-50">
          <div className="flex items-center justify-center">
            <div className="aspect-square grayscale-25 shadow-[1px_14px_21px_-6px_rgba(0,0,0,0.2)] h-[270px] w-[270px] md:h-[350px] md:w-[350px] h-600-img h-800-400-img overflow-hidden rounded-xl">
              {image ? (
                <img
                  src={image}
                  alt={current_track?.track.album?.name}
                  width={"160px"}
                  className={"object-cover rounded-xs h-full w-full bg-black"}
                />
              ) : (
                <Directory width={"100%"} height={"100%"} type={REF.ALBUM} />
              )}
            </div>
          </div>
          <div className="flex items-center justify-center mt-5">
            <h2 className="lg:text-4xl lg:mb-1 text-3xl font-semibold  max-w-80">
              {current_track?.track.name ? <ScrollingText text={current_track?.track.name} /> : getSourceName(source.type)}
            </h2>
          </div>

          {current_track?.track.artists.length ? (
            <div className="flex items-center justify-center mt-1">
              <div className="max-w-80">
                <ScrollingText
                  text={`${getArtists(current_track?.track.artists)} ${
                    current_track?.track.album?.name ? " · " + current_track?.track.album.name : ""
                  }`}
                />
              </div>
            </div>
          ) : (
            <></>
          )}

          <div className="mt-2 mb-2 w-full text-center">
            {["bluetooth", "spotify", "shairportsync", "snapcast"].includes(source.type) ? (
              <div className="flex justify-center w-full">
                <Source />
              </div>
            ) : current_track?.track?.albums?.length ? (
              <div className="flex items-center">
                <ScrollingText text={`${getAlbums(current_track?.track?.albums)}`} />
              </div>
            ) : (
              <></>
            )}
          </div>

          <div className="flex items-center justify-center mt-2 w-full ">
            <div className="mt-6 seek-slider max-w-800 w-100">
              <PositionSlider className={"rounded-full"} showElapsedNumber={true} />
            </div>
          </div>

          <div className="flex items-center justify-center mt-1 mb-9 w-full">
            <div className="max-w-300 w-100 flex justify-between items-center">
              <FavouriteButton />
              <div className="flex items-center">
                <ShuffleButton />
                <PreviousButton />
                <PlayPauseButton />
                <NextButton />
                <RepeatButton />
              </div>
              <ButtonQueue />
            </div>
          </div>
        </div>
        {/* End Vertical Layout */}

        {/* Start Horizontal Layout */}
        <div className="h-600-show -mt-[33px] px-5 relative z-50">
          <div className="flex items-center justify-center">
            <div
              className={`w-1/12 aspect-square md:w-[350px] h-600-img lg:mr-10 relative transition-all duration-500 ease-in-out transform ${
                playback_state === PLAYBACK_STATE.PLAYING ? "mr-10" : "mr-5"
              }`}
            >
              <img
                src="/assets/disc.png"
                className={`transition-transform duration-500 ease-in-out transform ${
                  playback_state === PLAYBACK_STATE.PLAYING ? "translate-x-7 animate-spin" : "translate-x-0"
                }`}
              />
              <div className="shadow-[1px_14px_21px_-6px_rgba(0,0,0,0.2)] absolute top-0 rounded-lg overflow-hidden h-full aspect-square">
                {image ? (
                  <img src={image} alt={current_track?.track.album?.name} className={"object-cover rounded-xs h-full w-full "} />
                ) : (
                  <Directory width={"100%"} height={"100%"} type={REF.ALBUM} />
                )}
              </div>
            </div>

            <div className={`w-11/12 overflow-hidden`}>
              <h2 className="lg:text-4xl lg:mb-1 text-2xl sm:text-3xl font-semibold">
                {current_track?.track.name ? <ScrollingText text={current_track?.track.name} /> : getSourceName(source.type)}
              </h2>

              {current_track?.track.artists.length ? (
                <div className="mt-2 flex items-center">
                  <UserIcon weight={ICON_WEIGHT} size={ICON_SM} className="mr-2" />
                  <ScrollingText
                    text={`${getArtists(current_track?.track.artists)} ${
                      current_track?.track.album?.name ? " · " + current_track?.track.album.name : ""
                    }`}
                  />
                </div>
              ) : (
                <></>
              )}

              <div className="mt-3">
                {["bluetooth", "spotify", "shairportsync", "snapcast"].includes(source.type) ? (
                  <Source />
                ) : current_track?.track?.albums?.length ? (
                  <div className="flex items-center">
                    <VinylRecordIcon weight={ICON_WEIGHT} size={ICON_SM} className="mr-2" />
                    <ScrollingText text={`${getAlbums(current_track?.track?.albums)}`} />
                  </div>
                ) : (
                  <></>
                )}
              </div>

              <div className="hidden sm:flex items-center mt-4 w-full">
                <div className="max-w-300 w-80 flex justify-between items-center">
                  <FavouriteButton />
                  <div className="flex items-center">
                    <ShuffleButton />
                    <PreviousButton />
                    <PlayPauseButton />
                    <NextButton />
                    <RepeatButton />
                  </div>
                  <ButtonQueue />
                </div>
              </div>
            </div>
          </div>
          <div className="items-center justify-center mt-2 w-full">
            <div className="flex justify-between items-center sm:hidden ">
              <FavouriteButton />
              <div className="flex items-center">
                <ShuffleButton />
                <PreviousButton />
                <PlayPauseButton />
                <NextButton />
                <RepeatButton />
              </div>
              <ButtonQueue />
            </div>
            <div className="mt-3 seek-slider md:max-w-800  w-full">
              <PositionSlider className={"rounded-full"} showElapsedNumber={true} />
            </div>
          </div>
        </div>
        {/* End Horizontal Layout */}
      </Page>
    </Overlay>
  );
};

export default React.memo(OverlayNowPlaying);
