import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { DIALOG_EVENTS } from "@/store/constants";

import Modal from "@/components/Modal";

const DialogEmptyLibrary = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const onClickHandler = () => {
    navigate("/storage");
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
  };

  return (
    <Modal
      title="Empty Library"
      onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })}
      isOpen={true}
      buttonText="Add Folders"
      buttonOnClick={onClickHandler}
    >
      <span className="text-secondary">
        Your music library is empty.
        <br />
        You can add music by going to 'Storage' section and then using the 'Add to Library' option.
      </span>
    </Modal>
  );
};

export default DialogEmptyLibrary;
