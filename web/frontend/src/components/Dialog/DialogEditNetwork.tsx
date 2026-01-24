import { useState } from "react";
import { useDispatch } from "react-redux";
import { NetworkConnectionInfo } from "@/types";
import { getNetworkDeviceName } from "@/util";
import { Input } from "@/components/Form/Input";
import { useNetworkActions } from "@/hooks/useNetworkActions";
import { Switch } from "../ui/switch";
import { DIALOG_EVENTS } from "@/store/constants";

import Modal from "@/components/Modal";

const DialogEditNetwork = ({ item }: { item: NetworkConnectionInfo }) => {
  const dispatch = useDispatch();
  const { modifyNetwork, loading } = useNetworkActions();

  const [ipv4_address, setIpv4_address] = useState<string>(item?.ipv4_address || "");
  const [ipv4_gateway, setIpv4_gateway] = useState<string>(item?.ipv4_gateway_runtime || "");
  const [ipv4_dns, setIpv4_dns] = useState<string>(item?.ipv4_dns_runtime || "");
  const [method, setMethod] = useState<string>(item?.ipv4_method);

  return (
    <Modal
      title="Configure Network"
      onClose={() => dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE })}
      isOpen={true}
      buttonText="Apply"
      buttonLoading={loading}
      buttonOnClick={() => modifyNetwork(item.device, item.name, ipv4_address, ipv4_gateway, ipv4_dns, method)}
      buttonDisabled={(ipv4_address === "" || ipv4_gateway === "" || ipv4_dns === "") && method === "manual"}
    >
      <div className="flex text-xl items-center">
        {getNetworkDeviceName(item.device)}
        {item.device}
      </div>
      <div className="pt-2 pb-4 text-secondary">
        Changing network settings may cause you to lose access. Please ensure your settings are correct before applying.
      </div>

      <div className="mb-3">
        <div className="mb-1">Auto using DHCP</div>
        <Switch value={method === "auto" ? true : false} onChange={(value) => setMethod(value ? "auto" : "manual")} />
      </div>

      <Input
        type="text"
        placeholder="IPv4 address"
        value={ipv4_address}
        onChange={(e) => setIpv4_address(e.target.value)}
        onClickClear={() => setIpv4_address("")}
        disabled={loading || method === "auto"}
      />

      <Input
        type="text"
        className="mt-4"
        placeholder="IPv4 gateway"
        value={ipv4_gateway}
        onChange={(e) => setIpv4_gateway(e.target.value)}
        onClickClear={() => setIpv4_gateway("")}
        disabled={loading || method === "auto"}
      />

      <Input
        type="text"
        className="mt-4"
        placeholder="IPv4 dns"
        value={ipv4_dns}
        onChange={(e) => setIpv4_dns(e.target.value)}
        onClickClear={() => setIpv4_dns("")}
        disabled={loading || method === "auto"}
      />
    </Modal>
  );
};

export default DialogEditNetwork;
