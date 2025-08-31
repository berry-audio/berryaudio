import { getBitDepth, getBitrate, getCodecName, getSampleRate } from "@/util";
import { DotIcon } from "@phosphor-icons/react";
import { useSelector } from "react-redux";

const StreamInfo = () => {
  const { current_track } = useSelector((state: any) => state.player);

  return (
    <div className="flex justify-center items-center">
      {current_track?.track?.audio_codec &&
        getCodecName(current_track?.track?.audio_codec)}
      {current_track?.track?.bitrate && (
        <>
          <DotIcon size={32} className="-mx-2" />
          {getBitrate(current_track?.track?.bitrate)}
        </>
      )}
      {current_track?.track.sample_rate && (
        <>
          <DotIcon size={32} className="-mx-2"/>
          {getSampleRate(current_track?.track.sample_rate as number)}
        </>
      )}
      {current_track?.track.bit_depth && (
        <>
          <DotIcon size={32} className="-mx-2"/>
          {getBitDepth(current_track?.track.bit_depth)}
        </>
      )}
    </div>
  );
};

export default StreamInfo;
