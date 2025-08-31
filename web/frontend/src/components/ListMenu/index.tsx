import { CaretRightIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import React from "react";
import Spinner from "../Spinner";
import ItemWrapper from "../Wrapper/ItemWrapper";
import ItemPadding from "../Wrapper/ItemPadding";

const ListMenu = ({
  name,
  icon,
  disabled,
  loading,
  onClick,
}: {
  name: string;
  icon: React.ReactNode;
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
}) => {
  return (
    <ItemWrapper>
      <button
        className="flex w-full justify-between cursor-pointer disabled:opacity-50"
        onClick={onClick}
        disabled={disabled}
      >
          <ItemPadding>
            <div className="flex items-center">
              <span className="mr-4 text-black dark:text-white">{icon}</span>
              <span>{name}</span>
            </div>
            <div className="flex items-center">
              {loading && <Spinner />}
              <CaretRightIcon weight={ICON_WEIGHT} size={ICON_SM} />
            </div>
          </ItemPadding>
      </button>
    </ItemWrapper>
  );
};

export default ListMenu;
