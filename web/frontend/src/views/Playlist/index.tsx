import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useDispatch } from "react-redux";
import { usePlaylistService } from "@/services/playlist";
import { MusicNoteIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { DIALOG_EVENTS } from "@/store/constants";
import { ACTIONS } from "@/constants/actions";
import { REF } from "@/constants/refs";
import { splitUri } from "@/util";
import { Playlist, Ref, ViewMode } from "@/types";

import Page from "@/components/Page";
import Spinner from "@/components/Spinner";
import ButtonLayoutToggle from "@/components/Button/ButtonLayoutToggle";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import SortableList from "@/components/SortableList";
import NoItems from "@/components/ListItem/NoItems";
import ButtonPlaylistCreate from "@/components/Button/ButtonPlaylistCreate";
import List from "@/components/InfiniteScroll/List";
import Grid from "@/components/InfiniteScroll/Grid";


const Playlists = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { getDirectory, getPlaylistItem, remove, move } = usePlaylistService();
  const { id } = useParams();

  const [playlist, setPlaylist] = useState<Playlist>();
  const [layout, setLayout] = useState<ViewMode>("list");
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchItem = async (uri: string) => {
    setPlaylist(undefined);
    setIsLoading(true);
    const item = await getPlaylistItem(uri);
    setPlaylist(item);
    setIsLoading(false);
  };

  const onClickPlaylistItem = async (item: Ref) => {
    const uri = splitUri(item.uri);
    navigate(`/playlist/${uri.id}`);
  };

  const onClickActionTrack = async (action: ACTIONS, tlid: number) => {
    if (action === ACTIONS.REMOVE) {
      const item = await remove(`playlist:${id}`, tlid);
      setPlaylist({ ...item });
    }
  };

  const onActionMove = async (
    start: number,
    end: number,
    to_position: number
  ) => {
    await move(`playlist:${id}`, start, end, to_position);
  };

  const onClickAction = async (action: string, item: Ref) => {
    switch (action) {
      case ACTIONS.RENAME:
        dispatch({
          type: DIALOG_EVENTS.DIALOG_PLAYLIST_RENAME,
          payload: item,
        });
        break;
      case ACTIONS.DELETE:
        dispatch({
          type: DIALOG_EVENTS.DIALOG_PLAYLIST_DELETE,
          payload: item,
        });
        break;
      default:
        dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
    }
  };

  useEffect(() => {
    if (id) {
      fetchItem(`playlist:${id}`);
    }
  }, [id]);

  return !id ? (
    <Page
      wfull={layout === "grid"}
      title={"Playlists"}
      rightComponent={
        <div className="flex items-center">
          <div className="mr-2">
            <ButtonLayoutToggle setLayoutype={setLayout} layoutType={layout} />
          </div>
          <div className="mr-4">
            <ButtonPlaylistCreate />
          </div>
        </div>
      }
      backButtonOnClick={() => navigate("/")}
      backButton
    >
      {layout === "list" && (
        <List
          query={REF.RADIO}
          getDirectory={getDirectory}
          onClickCallback={onClickPlaylistItem}
          onClickActionCallback={onClickAction}
        />
      )}
      {layout === "grid" && (
        <Grid
          query={REF.RADIO}
          getDirectory={getDirectory}
          onClickCallback={onClickPlaylistItem}
          onClickActionCallback={onClickAction}
        />
      )}
    </Page>
  ) : (
    <Page
      title={playlist?.name}
      backButtonOnClick={() => navigate("/playlist")}
      backButton
    >
      {isLoading ? (
        <LayoutHeightWrapper>
          <Spinner />
        </LayoutHeightWrapper>
      ) : playlist?.tracks.length ? (
        <SortableList
          tracks={playlist?.tracks}
          onMoveCallback={onActionMove}
          onActionCallback={onClickActionTrack}
        />
      ) : (
        <LayoutHeightWrapper>
          <NoItems
            title="Empty Playlist"
            desc={"No tracks here"}
            icon={<MusicNoteIcon weight={ICON_WEIGHT} size={ICON_SM} />}
          />
        </LayoutHeightWrapper>
      )}
    </Page>
  );
};

export default Playlists;
