import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import {
  DragDropContext,
  Droppable,
  Draggable,
  DropResult,
} from "@hello-pangea/dnd";
import { DotsSixVerticalIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { usePlaybackService } from "@/services/playback";
import { TlTrack } from "@/types";
import { ACTIONS } from "@/constants/actions";
import { REF } from "@/constants/refs";

import ListItem from "../ListItem";
import ItemWrapper from "../Wrapper/ItemWrapper";

const reorder = (list: TlTrack[], startIndex: number, endIndex: number) => {
  const result = Array.from(list);
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);
  return result;
};

export default function SortableList({
  tracks,
  onMoveCallback,
  onActionCallback,
}: {
  tracks: TlTrack[];
  onMoveCallback?: (start: number, end: number, to_position: number) => void;
  onActionCallback?: (action: ACTIONS, tlid: number) => void;
}) {
  const { current_track } = useSelector((state: any) => state.player);
  const { play } = usePlaybackService();

  const [items, setItems] = useState(tracks);
  const [selectedTlid, setSelectedTlid] = useState<number | null>(
    current_track?.tlid
  );
  const [isLoadingItem, setIsLoadingItem] = useState<number | null>(null);

  useEffect(() => {
    setItems(tracks);
  }, [tracks]);

  useEffect(() => {
    setSelectedTlid(current_track?.tlid);
  }, [current_track?.tlid]);

  const handleTrackClick = async (uri: string, tlid: number) => {
    setSelectedTlid(tlid);
    setIsLoadingItem(tlid);
    await play(uri, tlid);
    setIsLoadingItem(null);
  };

  const onDragEnd = (result: DropResult) => {
    if (!result.destination) return;

    onMoveCallback?.(
      result.source.index,
      result.source.index + 1,
      result.destination.index
    );

    const newItems: any = reorder(
      items,
      result.source.index,
      result.destination.index
    );
    setItems(newItems);
  };

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Droppable droppableId="droppable">
        {(provided) => (
          <div ref={provided.innerRef} {...provided.droppableProps}>
            {items.map((item, index) => (
              <Draggable
                key={`item-${item.tlid}`}
                draggableId={`item-${item.tlid}`}
                index={index}
              >
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                    className={`overflow-hidden md:overflow-visible ${
                      snapshot.isDragging
                        ? "bg-white dark:bg-neutral-950 rounded-md"
                        : ""
                    }`}
                  >
                    <ItemWrapper>
                      <DotsSixVerticalIcon
                        weight={ICON_WEIGHT}
                        size={ICON_SM}
                        className="-mr-3 ml-1"
                      />
                      <ListItem
                        className="hover:bg-transparent"
                        isPlaylist={true}
                        isLoading={item.tlid === isLoadingItem}
                        item={{ ...(item.track as any), type: REF.TRACK }}
                        selected={item.tlid === selectedTlid}
                        onClickCallback={() =>
                          handleTrackClick(item.track.uri, item.tlid)
                        }
                        onClickActionCallback={(action: ACTIONS) =>
                          onActionCallback?.(action, item.tlid)
                        }
                      />
                    </ItemWrapper>
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  );
}
