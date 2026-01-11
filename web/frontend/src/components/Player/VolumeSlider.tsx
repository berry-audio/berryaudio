import { useEffect, useState } from "react";
import { shallowEqual, useDispatch, useSelector } from "react-redux";
import { useMixerService } from "@/services/mixer";
import { Slider } from "@/components/Form/Slider";
import { INFO_EVENTS } from "@/store/constants";
import { EVENTS } from "@/constants/events";

import ButtonMuteToggle from "./ButtonMuteToggle";

/**
 * @description
 * `VolumeSlider` is a UI component for displaying and controlling the mixer's volume level.
 * It initializes volume when the WebSocket connects, listens to volume change events, and syncs changes to the backend.
 */
const VolumeSlider = ({ classname, onValueChange }: { classname?: string; onValueChange?: (value: number) => void }) => {
  const dispatch = useDispatch();
  const { volume } = useSelector((state: any) => state.player, shallowEqual);
  const { setMixerVolume } = useMixerService();

  const [mxVolumeSlider, setMxVolumeSlider] = useState<number | null>(volume);

  const onCommittedVolume = async ([value]: number[]) => {
    try {
      dispatch({ type: INFO_EVENTS.MIXER_VOLUME_DRAGGING, payload: false });
      dispatch({
        type: EVENTS.VOLUME_CHANGED,
        payload: {
          volume: value,
        },
      });
    } catch (error) {
      throw error;
    }
  };

  const onChangeVolume = ([value]: number[]) => {
    dispatch({ type: INFO_EVENTS.MIXER_VOLUME_DRAGGING, payload: true });
    setMxVolumeSlider(value);
    setMixerVolume(value);
    onValueChange?.(value);
  };

  const onMouseEnter = () => {
    dispatch({ type: INFO_EVENTS.MIXER_VOLUME_DRAGGING, payload: true });
  };

  const onMouseLeave = () => {
    dispatch({ type: INFO_EVENTS.MIXER_VOLUME_DRAGGING, payload: false });
  };

  useEffect(() => {
    setMxVolumeSlider(volume);
  }, [volume]);

  return (
    <div className="flex w-full ">
      <div className="mr-2 w-14">
        <ButtonMuteToggle />
      </div>
      <Slider
        value={[mxVolumeSlider as number]}
        max={100}
        step={1}
        className={`w-full rounded-full ${classname ? classname : ""}`}
        onValueChange={onChangeVolume}
        onValueCommit={onCommittedVolume}
        onMouseLeave={onMouseLeave}
        onPointerLeave={onMouseLeave}
        onMouseEnter={onMouseEnter}
        disabled={mxVolumeSlider === null}
      />
    </div>
  );
};

export default VolumeSlider;
