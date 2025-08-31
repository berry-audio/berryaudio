import { SpeakerHighIcon, SpeakerSlashIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { useMixerService } from "@/services/mixer";
import { useSelector } from "react-redux";

import ButtonIcon from "../Button/ButtonIcon";

const ButtonMuteToggle = () => {
  const { mute } = useSelector((state: any) => state.player);
  const { setMixerMute } = useMixerService();

  return (
    <ButtonIcon onClick={async () => await setMixerMute(!mute)}>
      {mute ? (
        <SpeakerSlashIcon size={ICON_SM} weight={ICON_WEIGHT} className="opacity-30"/>
      ) : (
        <SpeakerHighIcon size={ICON_SM} weight={ICON_WEIGHT} />
      )}
    </ButtonIcon>
  );
};

export default ButtonMuteToggle;
