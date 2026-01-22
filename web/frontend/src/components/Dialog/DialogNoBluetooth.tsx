import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { DIALOG_EVENTS } from "@/store/constants";

import Modal from "@/components/Modal";

const DialogNoBluetooth = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  return (
    <Modal
      title="Bluetooth"
      onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })}
      isOpen={true}
      buttonText="Connect"
      buttonOnClick={()=>navigate('/settings/bluetooth')}
    >
    <span className="text-secondary"> To play music, please connect to a Bluetooth device.</span>
    </Modal>
  );
};

export default DialogNoBluetooth;
