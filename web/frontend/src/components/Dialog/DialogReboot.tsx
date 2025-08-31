import { useState } from "react";
import { useDispatch } from "react-redux";
import { useSystemService } from "@/services/system";
import { DIALOG_EVENTS } from "@/store/constants";

import Modal from "@/components/Modal";

const DialogReboot = () => {
  const dispatch = useDispatch();

  const { setReboot } = useSystemService();

  const [buttonLoading, setButtonLoading] = useState<boolean>(false);

  const onClickHandler = async () => {
    setButtonLoading(true);
    await setReboot();
    setButtonLoading(false);
    dispatch({ type: DIALOG_EVENTS.DIALOG_REBOOT });
  };

  return (
    <Modal
      title="System"
      onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })}
      isOpen={true}
      buttonText="Reboot Now"
      buttonLoading={buttonLoading}
      buttonOnClick={onClickHandler}
    >
      In order for changes to take effect.You need to reboot system.
    </Modal>
  );
};

export default DialogReboot;
