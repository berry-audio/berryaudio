import { PlayIcon } from "@phosphor-icons/react";
import { usePlayNow } from "@/hooks/usePlayNow";
import { Ref } from "@/types";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";
import Spinner from "@/components/Spinner";

const ButtonPlayAll = ({ item }: { item: Ref }) => {
  const { handlePlayNow, loading } = usePlayNow();

  return (
    <ButtonIcon onClick={() => handlePlayNow(item)}>
      {loading ? (
        <Spinner />
      ) : (
        <PlayIcon
          weight={ICON_WEIGHT}
          size={ICON_SM}
          className="dark:text-white text-black"
        />
      )}
    </ButtonIcon>
  );
};

export default ButtonPlayAll;
