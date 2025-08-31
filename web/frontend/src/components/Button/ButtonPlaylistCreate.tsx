import { useState } from "react";
import { ListPlusIcon } from "@phosphor-icons/react";
import { useDispatch, useSelector } from "react-redux";
import { usePlaylistService } from "@/services/playlist";
import { Input } from "@/components/Form/Input";
import { INFO_EVENTS } from "@/store/constants";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import Modal from "@/components/Modal";
import ButtonIcon from "@/components/Button/ButtonIcon";


const ButtonPlaylistCreate = ({fromQueue = false} :{ fromQueue?:boolean}) => {
  const dispatch = useDispatch();

  const { createItem } = usePlaylistService();
  const { current_playlist } = useSelector((state: any) => state.player);

  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [playlistName, setPlaylistName] = useState<string>("My Mix");
  const [isLoading, setIsloading] = useState<boolean>(false);

  const onClickCreateHandler = async () => {
    setIsloading(true);
    const tl_tracks = fromQueue ? current_playlist : []
    await createItem(playlistName, tl_tracks);
    dispatch({ type: INFO_EVENTS.PLAYLISTS_UPDATED })
    setIsloading(false);
    setShowCreateModal(false);
  };

  const disabled = fromQueue && current_playlist.length <= 0;

  return (
    <>
      <ButtonIcon onClick={() => setShowCreateModal(true)} disabled={disabled}>
        <ListPlusIcon weight={ICON_WEIGHT} size={ICON_SM} />
      </ButtonIcon>

      <Modal
        title="New Playlist"
        onClose={() => setShowCreateModal(false)}
        isOpen={showCreateModal}
        buttonText="Create"
        buttonLoading={isLoading}
        buttonOnClick={onClickCreateHandler}
        buttonDisabled={playlistName === ''}
      >
          <Input
            type="text"
            placeholder="Playlist Name"
            value={playlistName}
            onChange={(e) => setPlaylistName(e.target.value)}
            onClickClear={()=>setPlaylistName('')}
          />
      </Modal>
    </>
  );
};

export default ButtonPlaylistCreate;
