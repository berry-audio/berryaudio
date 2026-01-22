import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useLocalService } from "@/services/local";
import { InfoIcon } from "@phosphor-icons/react";
import { DIALOG_EVENTS } from "@/store/constants";
import { ICON_WEIGHT } from "@/constants";

import Modal from "@/components/Modal";
import { useNavigate } from "react-router-dom";

const DialogScanLibrary = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { progress } = useSelector((state: any) => state.scan);
  const { setScan } = useLocalService();

  const [scanInProgress, setScanInProgress] = useState<boolean>(false);
  const [scanStatus, setScanStatus] = useState<boolean>(false);

  useEffect(() => {
    if (progress.completed) {
      setScanInProgress(false);
    }
  }, [progress]);

  const onClickScanLibrary = async () => {
    if (!scanInProgress && scanStatus) {
      navigate("/library");
      dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
      return;
    }

    if (await setScan()) {
      setScanStatus(true);
      setScanInProgress(true);
    }
  };

  return (
    <Modal
      title="Scan Library"
      onClose={() => {
        setScanStatus(false);
        dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
      }}
      isOpen={true}
      buttonText={scanInProgress ? "Scanning" : scanStatus ? "Go to Library" : "Start Scan"}
      buttonLoading={scanInProgress}
      buttonOnClick={onClickScanLibrary}
    >
      {scanStatus ? (
        <>
          {scanInProgress ? (
            <>
              <p className="text-secondary">Scan in progress — do not close this window.</p>
              <div className="flex items-center">
                <InfoIcon weight={ICON_WEIGHT} size={20} className="mr-1" />
                <span className="text-secondary">
                  Processed: {progress.processed} | Inserted: {progress.inserted} | Updated: {progress.updated}
                </span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center">
                <span className="text-secondary">Scan completed successfully.</span>
              </div>
              <div className="flex items-center">
                <InfoIcon weight={ICON_WEIGHT} size={20} className="mr-1" />
                <span className="text-secondary">
                  Processed: {progress.processed} | Inserted: {progress.inserted} | Updated: {progress.updated}
                </span>
              </div>
            </>
          )}
        </>
      ) : (
        <p className="text-secondary">
          Berryaudio is about to scan all assigned folders and update your library. This process may take some time. Do you want to continue?
        </p>
      )}
    </Modal>
  );
};

export default DialogScanLibrary;
