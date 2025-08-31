import React from "react";
import {
  MusicNotesMinusIcon,
  PenIcon,
  PlayIcon,
  PlaylistIcon,
  QueueIcon,
  StackPlusIcon,
  StarIcon,
  TrashIcon,
  UserIcon,
  VinylRecordIcon,
} from "@phosphor-icons/react";
import { useAddToQueue } from "@/hooks/useAddToQueue";
import { usePlayNow } from "@/hooks/usePlayNow";
import { useGoToArtist } from "@/hooks/useGoToArtist";
import { useGoToAlbum } from "@/hooks/useGoToAlbum";
import { useAddToPlaylist } from "@/hooks/useAddToPlaylist";
import { convertMillisecondstoTime, formatDate, getImage } from "@/util";
import { Ref } from "@/types";
import { ICON_WEIGHT, ICON_XS } from "@/constants";
import { ACTIONS } from "@/constants/actions";
import { REF } from "@/constants/refs";

import ItemPadding from "../Wrapper/ItemPadding";
import ActionMenu from "../Actions";
import CoverList from "./coverList";
import Cover from "./Cover";

const ListItem = ({
  item,
  view = REF.TRACK,
  isPlaylist = false,
  isLoading = false,
  cover,
  index = null,
  style,
  className,
  selected = false,
  onClickCallback,
  onClickActionCallback,
}: {
  item: Ref;
  cover?: boolean;
  view?: REF;
  isPlaylist?: boolean;
  isLoading?: boolean;
  index?: number | null;
  style?: {};
  className?: string;
  selected?: boolean;
  onClickCallback?: (item: Ref) => void;
  onClickActionCallback?: (action: ACTIONS, item: Ref) => void;
}) => {

  const { handleAddToQueue } = useAddToQueue();
  const { handlePlayNow } = usePlayNow();
  const { handleGoToArtist } = useGoToArtist();
  const { handleGoToAlbum } = useGoToAlbum();
  const { handleAddToPlaylist } = useAddToPlaylist();


  const itemsMenu = [
    {
      name: "Play Now",
      icon: <PlayIcon size={ICON_XS} weight={ICON_WEIGHT} />,
      hide: [REF.FOLDER].includes(item.type),
      action: () => handlePlayNow(item),
    },
    {
      name: "Add to Queue",
      icon: <QueueIcon size={ICON_XS} weight={ICON_WEIGHT} />,
      hide: [REF.FOLDER].includes(item.type),
      action: () => handleAddToQueue(item),
    },
    {
      name: "Rename",
      icon: <PenIcon size={ICON_XS} weight={ICON_WEIGHT} />,
      hide: ![REF.PLAYLIST].includes(item.type),
      action: () => onClickActionCallback?.(ACTIONS.RENAME, item),
    },
    {
      name: "Delete",
      icon: <TrashIcon size={ICON_XS} weight={ICON_WEIGHT} />,
      hide: ![REF.PLAYLIST].includes(item.type),
      action: () => onClickActionCallback?.(ACTIONS.DELETE, item),
    },
    {
      name: "Go to Artist",
      icon: <UserIcon size={ICON_XS} weight={ICON_WEIGHT} />,
      disabled: !item?.artists?.[0]?.uri,
      hide: item.type !== REF.TRACK,
      action: () => handleGoToArtist(item),
    },
    {
      name: "Go to Album",
      icon: <VinylRecordIcon size={ICON_XS} weight={ICON_WEIGHT} />,
      disabled: !item?.albums?.[0]?.uri,
      hide: item.type !== REF.TRACK,
      action: () => handleGoToAlbum(item),
    },
    {
      name: "Favourite",
      icon: <StarIcon size={ICON_XS} weight={ICON_WEIGHT} />,
      hide: [REF.FOLDER].includes(item.type),
      action: () => undefined,
      disabled: true
    },

    {
      name: "Add to Playlist",
      icon: <PlaylistIcon size={ICON_XS} weight={ICON_WEIGHT} />,
      hide: [REF.PLAYLIST, REF.FOLDER].includes(item.type),
      action: () => handleAddToPlaylist(item),
    },
    {
      name: "Remove",
      icon: <MusicNotesMinusIcon size={ICON_XS} weight={ICON_WEIGHT} />,
      hide: !([REF.TRACK].includes(item.type) && isPlaylist),
      action: () => onClickActionCallback?.(ACTIONS.REMOVE, item),
    },
    {
      name: "Add to Library",
      icon: <StackPlusIcon size={ICON_XS} weight={ICON_WEIGHT} />,
      hide: ![REF.FOLDER].includes(item.type),
      action: () => onClickActionCallback?.(ACTIONS.ADD_LIBRARY, item),
    },
  ];

  return cover ? (
    <div
      key={index}
      className={`cursor-pointer w-full relative ${className ? className : ""}`}
      style={{ ...style }}
    >
      <Cover
        type={item.type}
        loading={isLoading}
        title={item.name}
        subtitle={getSubtitle(item, view)}
        image={getImage(item.images?.[0]?.uri)}
        onClick={() => onClickCallback?.(item)}
        actions={<ActionMenu items={itemsMenu}/>}
      />
      
    </div>
  ) : (
    <>
      {/* Not a button else draggable wont work */}
      <div
        className="flex items-center w-full cursor-pointer justify-between relative"
        onClick={() => onClickCallback?.(item)}
      >
        <ItemPadding>
          <CoverList
            no={index === null ? undefined : index + 1}
            type={item.type}
            loading={isLoading}
            title={item.name}
            subtitle={getSubtitle(item, view)}
            duration={getDuration(item)}
            image={getImage(item.images?.[0]?.uri)}
            selected={selected}
          />
        </ItemPadding>
      </div>
      <div className="pr-2">
        <ActionMenu items={itemsMenu} />
      </div>
    </>
  );
};

export default React.memo(ListItem);

export const getDuration = (item: Ref): string | undefined => {
  switch (item.type) {
    case REF.TRACK:
      return item.length ? convertMillisecondstoTime(item.length) : undefined;
    case REF.PLAYLIST:
      return `${formatDate(item?.last_modified)}`;
    default:
      return undefined;
  }
};

export const getSubtitle = (item: Ref, view: REF): string => {
  switch (item.type) {
    case REF.TRACK:
    case REF.ALBUM:
      if (view === REF.ARTIST) {
        return item?.albums?.map((album: any) => album.name).join(",") || "...";
      }
      return item?.artists?.map((artist: any) => artist.name).join(",") || "";
    case REF.ARTIST:
    case REF.DIRECTORY:
    case REF.PLAYLIST:
      return `${String(item.length)} Tracks`;
    default:
      return "";
  }
};
