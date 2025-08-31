import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { DotsNineIcon } from "@phosphor-icons/react";
import { OVERLAY_EVENTS, DIALOG_EVENTS } from "@/store/constants";
import { ICON_SM } from "@/constants";

import Source from "../Source";
import DateTime from "../DateTime";
import ButtonIcon from "../Button/ButtonIcon";
import ButtonThemeToggle from "../Button/ButtonThemeToggle";
import ButtonSearch from "../Button/ButtonSearch";
import ButtonVolume from "../Player/ButtonVolume";

export function Menu() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { source } = useSelector((state: any) => state.player);

  const onClickMenuHandler = () => {
    dispatch({ type: OVERLAY_EVENTS.OVERLAY_CLOSE });
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
    navigate("/");
  };

  return (
    <div className="rounded-none px-4 h-12 flex justify-between items-center shadow-none relative text-lg">
      <div className="flex items-center ">
        <ButtonIcon onClick={onClickMenuHandler}>
          <DotsNineIcon size={ICON_SM} weight={"bold"} />
        </ButtonIcon>
        <span className="pr-4 pl-1 scale-90">
          <DateTime time />
        </span>
      </div>

      <div className="flex items-center">
        <div className="mr-1">
          <ButtonSearch />
        </div>
        {source?.state?.connected && (
          <div className="mr-2 ml-1">
            <Source hideText={true} className="scale-90" />
          </div>
        )}
        <ButtonThemeToggle />
        <ButtonVolume />
      </div>
    </div>
  );
}
