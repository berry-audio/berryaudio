import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { InfoIcon } from "@phosphor-icons/react";
import { useLibraryInfo } from "@/hooks/useLibraryInfo";
import { Ref } from "@/types";

import ButtonIcon from "@/components/Button/ButtonIcon";

const ButtonInfo = ({ item }: { item: Ref }) => {
  const { handleArtistInfo } = useLibraryInfo();

  return (
    <ButtonIcon onClick={() => handleArtistInfo(item)}>
      <InfoIcon
        weight={ICON_WEIGHT}
        size={ICON_SM}
        className="dark:text-white text-black"
      />
    </ButtonIcon>
  );
};

export default ButtonInfo;
