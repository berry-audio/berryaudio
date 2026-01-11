import { useDispatch } from "react-redux";
import { DIALOG_EVENTS } from "@/store/constants";
import { Ref } from "@/types";

import Modal from "@/components/Modal";

const DialogLibraryInfo = ({ item }: { item: Ref }) => {
  const dispatch = useDispatch();

  return (
    <Modal title={item.name} onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })} isOpen={true} buttonShow={false}>
      <span className="text-secondary">{item.comment ? item.comment : "No information available"}</span>
    </Modal>
  );
};

export default DialogLibraryInfo;
