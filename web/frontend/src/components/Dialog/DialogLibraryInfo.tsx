import { useDispatch } from "react-redux";
import { DIALOG_EVENTS } from "@/store/constants";
import { Ref } from "@/types";

import Modal from "@/components/Modal";

const DialogLibraryInfo = ({ item }: { item: Ref }) => {
  const dispatch = useDispatch();

  console.log(item);
  return (
    <Modal
      title={item.name}
      onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })}
      isOpen={true}
      buttonShow={false}
    >
      <div>{item.comment ? item.comment : "No information available"}</div>
    </Modal>
  );
};

export default DialogLibraryInfo;
