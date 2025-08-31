import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { OVERLAY_EVENTS } from "@/store/constants";

import Overlay from ".";
import DateTime from "../DateTime";
import ButtonWake from "../Button/ButtonWake";

const OverlayStandby = () => {
  const dispatch = useDispatch();

  const { power_state } = useSelector((state: any) => state.system);

  useEffect(() => {
    if (!power_state.standby) dispatch({ type: OVERLAY_EVENTS.OVERLAY_CLOSE });
  }, [power_state]);

  return (
    <Overlay zindex={100} show={power_state.standby} overlay>
      <div className="top-5 right-5 absolute"><ButtonWake/></div>
      <div>
        <div className="items-center justify-center flex w-full h-full text-6xl">
          <DateTime time />
        </div>
        <div className="items-center justify-center flex w-full h-full text-[20px] font-extralight">
          <DateTime weekday />
        </div>
      </div>
    </Overlay>
  );
};

export default OverlayStandby;
