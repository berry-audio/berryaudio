import { JSX } from "react";
import { QueueIcon } from "@phosphor-icons/react";
import { useSelector } from "react-redux";
import { useTracklistService } from "@/services/tracklist";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { ACTIONS } from "@/constants/actions";

import ButtonPlaylistCreate from "@/components/Button/ButtonPlaylistCreate";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import SortableList from "@/components/SortableList";
import NoItems from "@/components/ListItem/NoItems";
import Page from "@/components/Page";
import ButtonQueueClear from "@/components/Button/ButtonQueueClear";

/**
 * Queue - Displays a draggable and sortable current of tracks.
 *
 * - Fetches tracklist from the server via WebSocket connection.
 * - Allows reordering of tracks using drag-and-drop.
 * - Clicking on a track starts playback.
 * @returns {JSX.Element} Playlist UI component
 */
const Queue = (): JSX.Element => {
  const { current_playlist } = useSelector((state: any) => state.player);
  const { move, remove } = useTracklistService();

  const onActionCallbackHandler = (action:ACTIONS, tlid:number) => {
    if(action === ACTIONS.REMOVE){
      remove(tlid);
    }
  }

  return (
    <Page
      backButton
      title="Now Playing"
      rightComponent={
        <div className="flex">
          <div className="mr-2"><ButtonQueueClear /></div>
           <div className="mr-4"><ButtonPlaylistCreate fromQueue={true}/></div>
        </div>
      }
    >
      {current_playlist?.length > 0 ? (
        <SortableList
          tracks={current_playlist}
          onActionCallback={onActionCallbackHandler}
          onMoveCallback={move}
        />
      ) : (
        <LayoutHeightWrapper>
          <NoItems
            title="No tracks in queue"
            desc={"Add some music"}
            icon={<QueueIcon weight={ICON_WEIGHT} size={ICON_SM} />}
          />
        </LayoutHeightWrapper>
      )}
    </Page>
  );
};

export default Queue;
