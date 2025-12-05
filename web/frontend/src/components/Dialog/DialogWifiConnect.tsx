import { useDispatch } from "react-redux";
import { DIALOG_EVENTS } from "@/store/constants";
import { WifiNetwork } from "@/types";
import { Input } from "@/components/Form/Input";
import { useState } from "react";
import { useNetworkActions } from "@/hooks/useNetworkActions";

import Modal from "@/components/Modal";
import { WifiHighIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

const DialogWifiConnect = ({ item }: { item: WifiNetwork }) => {
  const dispatch = useDispatch();
  const [password, setPassword] = useState<string>("");

  const { handleConnectAuth, loading } = useNetworkActions();

  return (
    <Modal
      title="Connect to Wi-Fi Network"
      onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })}
      isOpen={true}
      buttonText="Connect"
      buttonLoading={loading}
      buttonOnClick={() => handleConnectAuth(item.ssid, password)}
      buttonDisabled={password === ""}
    >
      <div className="mb-4 flex">
        <WifiHighIcon className="mr-2" weight={ICON_WEIGHT} size={ICON_SM} />
        {item.ssid}
      </div>

      <Input type="text" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} onClickClear={() => setPassword("")} disabled={loading} />
    </Modal>
  );
};

export default DialogWifiConnect;
