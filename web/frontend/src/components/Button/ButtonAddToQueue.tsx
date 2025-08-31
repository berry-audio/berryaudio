import { Ref } from "@/types";
import { PlusIcon } from "@phosphor-icons/react";
import { useAddToQueue } from "@/hooks/useAddToQueue";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";
import Spinner from "@/components/Spinner";

const ButtonAddToQueue = ({ item }: { item: Ref }) => {
  const { handleAddToQueue, loading } = useAddToQueue();

  return (
    <ButtonIcon onClick={() => handleAddToQueue(item)} className="mr-1">
      {loading ? (
        <Spinner />
      ) : (
        <PlusIcon
          weight={ICON_WEIGHT}
          size={ICON_SM}
          className="dark:text-white text-black"
        />
      )}
    </ButtonIcon>
  );
};

export default ButtonAddToQueue;
