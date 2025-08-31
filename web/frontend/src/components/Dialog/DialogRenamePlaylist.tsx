import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { Ref } from "@/types";
import { Input } from "@/components/Form/Input";
import { usePlaylistService } from "@/services/playlist";
import { INFO_EVENTS, DIALOG_EVENTS } from "@/store/constants";

import Modal from "@/components/Modal";

const DialogRenamePlaylist = ({ item }: { item: Ref }) => {
  const dispatch = useDispatch();

  const { editItem } = usePlaylistService();

  const [playlistName, setPlaylistName] = useState<string>(item?.name ?? "");
  const [buttonLoading, setButtonLoading] = useState<boolean>(false);

  const onClickEditPlaylist = async () => {
    setButtonLoading(true);
    await editItem(item?.uri as string, playlistName);
    dispatch({ type: INFO_EVENTS.PLAYLISTS_UPDATED });
    setButtonLoading(false);
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
  };

  useEffect(() => {
    setPlaylistName(item?.name);
  }, [item?.name]);

  return (
    <Modal
      title="Rename Playlist"
      onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })}
      isOpen={true}
      buttonText="Rename"
      buttonLoading={buttonLoading}
      buttonOnClick={onClickEditPlaylist}
      buttonDisabled={playlistName === ""}
    >
     
        <Input
          type="text"
          placeholder="Playlist Name"
          value={playlistName}
          onChange={(e) => setPlaylistName(e.target.value)}
          onClickClear={() => setPlaylistName("")}
        />
     
    </Modal>
  );
};

export default DialogRenamePlaylist;
