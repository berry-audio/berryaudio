import { DIALOG_EVENTS } from "@/store/constants";
import { useSelector } from "react-redux";

import DialogAddToPlaylist from "@/components/Dialog/DialogAddToPlaylist";
import DialogRenamePlaylist from "@/components/Dialog/DialogRenamePlaylist";
import DialogDeletePlaylist from "@/components/Dialog/DialogDeletePlaylist";
import DialogClearLibrary from "@/components/Dialog/DialogClearLibrary";
import DialogScanLibrary from "./DialogScanLibrary";
import DialogScanArtist from "./DialogScanArtist";
import DialogNoBluetooth from "./DialogNoBluetooth";
import DialogEmptyLibrary from "./DialogEmptyLibrary";
import DialogLibraryInfo from "./DialogLibraryInfo";
import DialogReboot from "./DialogReboot";
import DialogPowerOptions from "./DialogPowerOptions";
import DialogError from "./DialogError";
import DialogEditNetwork from "./DialogEditNetwork";
import DialogWifiAuth from "./DialogWifiAuth";

const Dialog = () => {
  const { dialog, payload: item } = useSelector((state: any) => state.dialog);

  return (
    <>
      {dialog === DIALOG_EVENTS.DIALOG_ERROR && (
        <DialogError item={item}/>
      )}
      {dialog === DIALOG_EVENTS.DIALOG_PLAYLISTS && (
        <DialogAddToPlaylist item={item} />
      )}
      {dialog === DIALOG_EVENTS.DIALOG_PLAYLIST_RENAME && (
        <DialogRenamePlaylist item={item} />
      )}
      {dialog === DIALOG_EVENTS.DIALOG_PLAYLIST_DELETE && (
        <DialogDeletePlaylist item={item} />
      )}
      {dialog === DIALOG_EVENTS.DIALOG_CLEAR_LIBRARY && <DialogClearLibrary />}
      {dialog === DIALOG_EVENTS.DIALOG_SCAN_LIBRARY && <DialogScanLibrary />}
      {dialog === DIALOG_EVENTS.DIALOG_SCAN_LIBRARY_ARTIST && (
        <DialogScanArtist />
      )}
      {dialog === DIALOG_EVENTS.DIALOG_BLUETOOTH_NOT_CONNECTED && (
        <DialogNoBluetooth />
      )}
      {dialog === DIALOG_EVENTS.DIALOG_WIFI_AUTH && (
        <DialogWifiAuth item={item}/>
      )}
      {dialog === DIALOG_EVENTS.DIALOG_EDIT_NETWORK && (
        <DialogEditNetwork item={item}/>
      )}
      {dialog === DIALOG_EVENTS.DIALOG_REBOOT && <DialogReboot />}
      {dialog === DIALOG_EVENTS.DIALOG_POWER_OPTIONS && <DialogPowerOptions />}
      {dialog === DIALOG_EVENTS.DIALOG_ADD_LIBRARY && <DialogEmptyLibrary />}
      {dialog === DIALOG_EVENTS.DIALOG_INFO_LIBRARY && (
        <DialogLibraryInfo item={item} />
      )}
    </>
  );
};

export default Dialog;
