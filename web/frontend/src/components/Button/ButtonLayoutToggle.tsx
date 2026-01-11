import { DotsNineIcon, ListBulletsIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "./ButtonIcon";

interface ButtonLayoutToggle {
  layoutType: "list" | "grid";
  setLayoutype: (type: "list" | "grid") => void;
}

const ButtonLayoutToggle = ({ layoutType, setLayoutype }: ButtonLayoutToggle) => {
  return (
    <div className="flex h-[50px] items-center">
      {layoutType === "list" ? (
        <ButtonIcon onClick={() => setLayoutype("grid")}>
          <DotsNineIcon weight={ICON_WEIGHT} size={ICON_SM} />
        </ButtonIcon>
      ) : (
        <ButtonIcon onClick={() => setLayoutype("list")}>
          <ListBulletsIcon weight={ICON_WEIGHT} size={ICON_SM} />
        </ButtonIcon>
      )}
    </div>
  );
};

export default ButtonLayoutToggle;
