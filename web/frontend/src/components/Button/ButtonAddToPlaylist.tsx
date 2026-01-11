import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { Ref } from "@/types";
import { PlaylistIcon } from "@phosphor-icons/react";
import { useAddToPlaylist } from "@/hooks/useAddToPlaylist";

import ButtonIcon from "@/components/Button/ButtonIcon";

const ButtonAddToPlaylist = ({ item }: { item: Ref }) => {
  const { handleAddToPlaylist } = useAddToPlaylist();

  return (
    <ButtonIcon onClick={() => handleAddToPlaylist(item)}>
      <PlaylistIcon weight={ICON_WEIGHT} size={ICON_SM} />
    </ButtonIcon>
  );
};

export default ButtonAddToPlaylist;
