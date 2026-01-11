import { FolderSimpleIcon, MusicNoteSimpleIcon, PlaylistIcon, UserIcon, VinylRecordIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { REF } from "@/constants/refs";

/**
 * Renders an icon representing the type of media item (e.g., track, album, artist).
 *
 * @component
 * @param {Object} props - The component props.
 * @param {string} props.type - The type of media item ('track', 'album', 'artist', 'directory').
 * @param {number} [props.width=50] - The width of the icon container in pixels.
 * @param {number} [props.height=50] - The height of the icon container in pixels.
 * @returns {JSX.Element} A styled icon inside a container div.
 */
const Directory = ({ type, width = "auto", height = "auto" }: { type?: REF; width?: number | string; height?: number | string }) => {
  const getIconByType = (type?: string) => {
    switch (type) {
      case REF.DIRECTORY:
        return <FolderSimpleIcon weight={ICON_WEIGHT} size={ICON_SM} />;
      case REF.ARTIST:
        return <UserIcon weight={ICON_WEIGHT} size={ICON_SM} />;
      case REF.TRACK:
        return <MusicNoteSimpleIcon weight={ICON_WEIGHT} size={ICON_SM} />;
      case REF.ALBUM:
        return <VinylRecordIcon weight={ICON_WEIGHT} size={ICON_SM} />;
      case REF.PLAYLIST:
        return <PlaylistIcon weight={ICON_WEIGHT} size={ICON_SM} />;
      default:
        return <FolderSimpleIcon weight={ICON_WEIGHT} size={ICON_SM} />;
    }
  };

  return (
    <div
      style={{ width, height }}
      className={`bg-neutral-900 dark:bg-neutral-800  text-white  flex items-center justify-center aspect-square w-full overflow-hidden ${
        type === REF.ALBUM ? "grayscale-25 bg-radial-[at_15%_5%] from-yellow-700 to-yellow-950" : "grayscale-25"
      }`}
    >
      {getIconByType(type)}
    </div>
  );
};

export default Directory;
