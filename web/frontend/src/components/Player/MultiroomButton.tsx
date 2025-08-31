import ButtonIcon from "@/components/Button/ButtonIcon";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { SpeakerHifiIcon } from "@phosphor-icons/react";

const MultiroomButton = () => {
  return (
    <ButtonIcon>
      <SpeakerHifiIcon size={ICON_SM} weight={ICON_WEIGHT} />
    </ButtonIcon>
  );
};

export default MultiroomButton;
