import { QueueIcon } from "@phosphor-icons/react";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { OVERLAY_EVENTS } from "@/store/constants";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "@/components/Button/ButtonIcon";

/**
 * Button component that navigates the user to the playlist page.
 *
 * @returns {JSX.Element} The rendered playlist navigation button.
 */
const ButtonQueue = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const onClickHandler = ()=>{
    dispatch({ type: OVERLAY_EVENTS.OVERLAY_CLOSE })
    navigate("/queue")
  }

  return (
    <ButtonIcon onClick={onClickHandler}>
      <QueueIcon weight={ICON_WEIGHT} size={ICON_SM} />
    </ButtonIcon>
  );
};

export default ButtonQueue;
