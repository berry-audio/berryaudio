import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { useMixerService } from "@/services/mixer";
import { Slider } from "@/components/Form/Slider";

import ButtonMuteToggle from "./ButtonMuteToggle";

/**
 * @description
 * `VolumeSlider` is a UI component for displaying and controlling the mixer's volume level.
 * It initializes volume when the WebSocket connects, listens to volume change events, and syncs changes to the backend.
 */
const VolumeSlider = ({classname}: {classname?:string}) => {
  const { volume } = useSelector((state: any) => state.player);
  const { setMixerVolume } = useMixerService();

  const [mxVolumeSlider, setMxVolumeSlider] = useState<number | null>(volume);

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
        className={`w-full rounded-full ${classname ? classname : ''}`}
        onValueChange={([value]) =>  setMixerVolume(value)}
        disabled={mxVolumeSlider === null}
      />
    </div>
  );
};

export default VolumeSlider;
