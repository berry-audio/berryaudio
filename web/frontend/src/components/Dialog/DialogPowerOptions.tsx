import { useState } from "react";
import { useDispatch } from "react-redux";
import { useSystemService } from "@/services/system";
import { DIALOG_EVENTS } from "@/store/constants";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { ArrowsClockwiseIcon, PowerIcon, RadioButtonIcon } from "@phosphor-icons/react";

import Modal from "@/components/Modal";
import ButtonIcon from "../Button/ButtonIcon";
import Spinner from "../Spinner";

const DialogPowerOptions = () => {
  const dispatch = useDispatch();
  const { setStandby, setReboot, setShutdown } = useSystemService();
  const [isLoading, setIsLoading] = useState<string>("");

  const onClickRebootHandler = async () => {
    setIsLoading("reboot");
    await setReboot();
    setIsLoading("");
  };

  const onClickStandbyHandler = async () => {
    setIsLoading("standby");
    await setStandby(true);
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
    setIsLoading("");
  };

  const onClickShutdownHandler = async () => {
    setIsLoading("shutdown");
    await setShutdown();
    setIsLoading("");
  };

  return (
    <Modal title="System" onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })} isOpen={true} buttonShow={false}>
      <div className="flex justify-between px-10">
        <div className="flex flex-col items-center">
          <ButtonIcon onClick={onClickStandbyHandler}>
            {isLoading === "standby" ? <Spinner /> : <PowerIcon weight={ICON_WEIGHT} size={ICON_SM} />}
          </ButtonIcon>
          <div className="mt-2 text-center">Standby</div>
        </div>

        <div className="flex flex-col items-center">
          <ButtonIcon onClick={onClickShutdownHandler}>
            {isLoading === "shutdown" ? <Spinner /> : <RadioButtonIcon weight={ICON_WEIGHT} size={ICON_SM} />}
          </ButtonIcon>
          <div className="mt-2 text-center">Power Off</div>
        </div>
        <div className="flex flex-col items-center">
          <ButtonIcon onClick={onClickRebootHandler}>
            {isLoading === "reboot" ? <Spinner /> : <ArrowsClockwiseIcon weight={ICON_WEIGHT} size={ICON_SM} />}
          </ButtonIcon>
          <div className="mt-2 text-center">Reboot</div>
        </div>
      </div>
    </Modal>
  );
};

export default DialogPowerOptions;
