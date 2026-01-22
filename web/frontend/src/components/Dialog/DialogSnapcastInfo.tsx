import { useDispatch, useSelector } from "react-redux";
import { DIALOG_EVENTS } from "@/store/constants";

import Modal from "@/components/Modal";

const DialogSnapcastInfo = () => {
  const dispatch = useDispatch();
  const { status } = useSelector((state: any) => state.snapcast);

  const ListItem = ({ title, desc }: { title: string; desc: string }) => {
    return (
      <div className="flex mt-2 text-secondary">
        <div className="w-25 flex font-medium">{title}:</div>
        <div className="flex-1 flex flex-col">{desc}</div>
      </div>
    );
  };

  return (
    <Modal title={"Connection Info"} onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })} isOpen={true} buttonShow={false}>
      {status?.server ? (
        <>
          <ListItem title="Name" desc={status?.server?.host?.name} />
          <ListItem title="IP" desc={status?.server?.host?.ip} />
          <ListItem title="OS" desc={status?.server?.host?.os} />
          <ListItem title="Software" desc={`${status?.server?.snapserver?.name} ${status?.server?.snapserver?.version} (${status?.server?.host?.arch})`} />
        </>
      ): (
        <div className="text-secondary">Server information unavailable</div>
      )}
    </Modal>
  );
};

export default DialogSnapcastInfo;
