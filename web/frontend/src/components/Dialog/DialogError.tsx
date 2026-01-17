import { useDispatch } from "react-redux";
import { DIALOG_EVENTS } from "@/store/constants";

import Modal from "@/components/Modal";

const DialogError = ({ item }: { item: any }) => {
  const dispatch = useDispatch();

  const onClickClose = async () => {
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
  };

  return (
    <Modal
      title="Something Went Wrong"
      onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })}
      isOpen={true}
      buttonText="Close"
      buttonOnClick={onClickClose}
    >
     <div className="text-muted"> {item.message || "An unknown error occurred."}</div>
    </Modal>
  );
};

export default DialogError;
