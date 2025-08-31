import { useState } from "react";
import { useDispatch } from "react-redux";
import { useLocalService } from "@/services/local";
import { DIALOG_EVENTS } from "@/store/constants";

import Modal from "@/components/Modal";

const DialogClearLibrary = () => {
  const dispatch = useDispatch();

  const { setClean } = useLocalService();
  const [buttonLoading, setButtonLoading] = useState<boolean>(false);

  const onClickClearLibrary = async () => {
    setButtonLoading(true);
    await setClean();
    setButtonLoading(false);
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
  };

  return (
    <Modal
      title="Clear Library"
      onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })}
      isOpen={true}
      buttonText="Clear"
      buttonLoading={buttonLoading}
      buttonOnClick={onClickClearLibrary}
    >
      Are you sure you want to clear your library? <br /> This cannot be undone.
    </Modal>
  );
};

export default DialogClearLibrary;
