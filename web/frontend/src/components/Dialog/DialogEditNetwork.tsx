import { useState } from "react";
import { useDispatch } from "react-redux";
import { NetworkDevice } from "@/types";
import { getNetworkDeviceName } from "@/util";
import { Input } from "@/components/Form/Input";
import { useNetworkActions } from "@/hooks/useNetworkActions";
import { DIALOG_EVENTS } from "@/store/constants";

import Modal from "@/components/Modal";

const DialogEditNetwork = ({ item }: { item: NetworkDevice }) => {
  const dispatch = useDispatch();

  const { modifyNetwork, loading } = useNetworkActions();

  const [ipv4_address, setIpv4_address] = useState<string>(item.ipv4_address || "");
  const [ipv4_gateway, setIpv4_gateway] = useState<string>(item.ipv4_gateway || "");
  const [ipv4_dns, setIpv4_dns] = useState<string>(item.ipv4_dns || "" );
  const [method, setMethod] = useState<string>("manual");

  return (
    <Modal
      title="Configure Network"
      onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })}
      isOpen={true}
      buttonText="Apply"
      buttonLoading={loading}
      buttonOnClick={() => modifyNetwork(item.device, item.connection, ipv4_address, ipv4_gateway, ipv4_dns, method )}
      buttonDisabled={ipv4_address === ""}
    >
      <div className="flex">{getNetworkDeviceName(item)}</div>
      <div className="pt-2 pb-4 text-neutral-500 text-sm">Changing network settings may cause you to lose access. Please ensure your settings are correct before applying.</div>

      <Input
        type="text"
        placeholder="IPv4 address"
        value={ipv4_address}
        onChange={(e) => setIpv4_address(e.target.value)}
        onClickClear={() => setIpv4_address("")}
        disabled={loading}
      />

      <Input
        type="text"
        className="mt-4"
        placeholder="IPv4 gateway"
        value={ipv4_gateway}
        onChange={(e) => setIpv4_gateway(e.target.value)}
        onClickClear={() => setIpv4_gateway("")}
        disabled={loading}
      />

      <Input
        type="text"
        className="mt-4"
        placeholder="IPv4 dns"
        value={ipv4_dns}
        onChange={(e) => setIpv4_dns(e.target.value)}
        onClickClear={() => setIpv4_dns("")}
        disabled={loading}
      />
    </Modal>
  );
};

export default DialogEditNetwork;
