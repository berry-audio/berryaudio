import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useLocalService } from "@/services/local";
import { DIALOG_EVENTS } from "@/store/constants";
import { InfoIcon } from "@phosphor-icons/react";
import { ICON_WEIGHT } from "@/constants";

import Modal from "@/components/Modal";

const DialogScanArtist = () => {
  const dispatch = useDispatch();

  const { progress } = useSelector((state: any) => state.scan);
  const { setScanArtists } = useLocalService();

  const [isScanInProgress, seIsScanInProgress] = useState<boolean>(false);
  const [scanStatus, setScanStatus] = useState<boolean>(false);

  useEffect(() => {
    if (progress.completed) {
      seIsScanInProgress(false);
    }
  }, [progress]);

  const onClickScanArtistLibrary = async () => {
    if (await setScanArtists()) {
      setScanStatus(true);
      seIsScanInProgress(true);
    }
  };

  return (
    <Modal
      title="Artist Information"
      onClose={() =>
        dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE }) && setScanStatus(false)
      }
      isOpen={true}
      buttonText="Start Download"
      buttonLoading={isScanInProgress}
      buttonOnClick={onClickScanArtistLibrary}
    >
      {scanStatus ? (
        <>
          {isScanInProgress ? (
            <>
              <p>Scan in progress — do not close this window.</p>
              <div className="flex items-center">
                <InfoIcon weight={ICON_WEIGHT} size={20} className="mr-1" />
                <span>
                  Updated: {progress.updated} | Downloaded:{" "}
                  {progress.downloaded} | N/A: {progress.unavailable}
                </span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center">
                <span>Scan completed successfully.</span>
              </div>
              <div className="flex items-center">
                <InfoIcon weight={ICON_WEIGHT} size={20} className="mr-1" />
                <span>
                  Updated: {progress.updated} | Downloaded:{" "}
                  {progress.downloaded} | N/A: {progress.unavailable}
                </span>
              </div>
            </>
          )}
        </>
      ) : (
        <p>
          Berryaudio will now scan your music library and fetch artist
          information automatically from AudioDB.com. This may take a few
          minutes — Continue?
        </p>
      )}
    </Modal>
  );
};

export default DialogScanArtist;
