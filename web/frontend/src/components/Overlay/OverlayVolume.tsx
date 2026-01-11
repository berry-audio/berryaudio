import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { OVERLAY_EVENTS } from "@/store/constants";
import { XIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import VolumeSlider from "../Player/VolumeSlider";
import ButtonIcon from "../Button/ButtonIcon";
import Overlay from ".";

const OverlayVolume = () => {
  const dispatch = useDispatch();

  const { overlay } = useSelector((state: any) => state.overlay);
  const { volume } = useSelector((state: any) => state.player);

  const [mixerVolume, setMixerVolume] = useState<number>(volume);

  return (
    <Overlay zindex={100} show={overlay === OVERLAY_EVENTS.OVERLAY_VOLUME} overlay>
      <div className="top-5 right-5 absolute">
        <ButtonIcon onClick={() => dispatch({ type: OVERLAY_EVENTS.OVERLAY_CLOSE })}>
          <XIcon size={ICON_SM} weight={ICON_WEIGHT} />
        </ButtonIcon>
      </div>
      <div className="w-full -ml-5 lg:w-100 items-center flex-col justify-center px-10 ">
        <VolumeSlider classname="volume-slider-overlay" onValueChange={(value) => setMixerVolume(value)} />
        <div className="ml-10 text-2xl">{mixerVolume}</div>
      </div>
    </Overlay>
  );
};

export default OverlayVolume;
