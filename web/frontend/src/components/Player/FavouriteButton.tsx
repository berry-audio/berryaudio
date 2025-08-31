import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { StarIcon } from "@phosphor-icons/react";

import ButtonIcon from "@/components/Button/ButtonIcon";

const FavouriteButton = () => {
  return (
    <ButtonIcon disabled>
      <StarIcon weight={ICON_WEIGHT} size={ICON_SM} />
    </ButtonIcon>
  );
};

export default FavouriteButton;
