import { useState } from "react";
import { useDispatch } from "react-redux";
import { Ref } from "@/types";
import { usePlaylistService } from "@/services/playlist";
import { INFO_EVENTS, DIALOG_EVENTS } from "@/store/constants";

import Modal from "@/components/Modal";

const DialogDeletePlaylist = ({ item }: { item: Ref }) => {
  const dispatch = useDispatch();

  const { deleteItem } = usePlaylistService();

  const [buttonLoading, setButtonLoading] = useState<boolean>(false);

  const onClickDeletePlaylist = async () => {
    setButtonLoading(true);
    await deleteItem(item?.uri as string);
    dispatch({ type: INFO_EVENTS.PLAYLISTS_UPDATED });
    setButtonLoading(false);
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
  };

  return (
    <Modal
      title="Delete Playlist"
      onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })}
      isOpen={true}
      buttonText="Delete"
      buttonLoading={buttonLoading}
      buttonOnClick={onClickDeletePlaylist}
    >
      <span className="text-secondary">
        Are you sure you want to delete playlist <i>{item.name}</i>?
      </span>
    </Modal>
  );
};

export default DialogDeletePlaylist;
