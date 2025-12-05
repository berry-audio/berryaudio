import {
  LaptopIcon,
  LockIcon,
  NetworkIcon,
  PencilIcon,
  TrashSimpleIcon,
  WifiHighIcon,
  WifiLowIcon,
  WifiMediumIcon,
  WifiNoneIcon,
  WifiSlashIcon,
} from "@phosphor-icons/react";
import { useSelector } from "react-redux";
import { useEffect, useState } from "react";
import { NetworkDevice, WifiNetwork } from "@/types";
import { useNetworkActions } from "@/hooks/useNetworkActions";
import { ICON_SM, ICON_WEIGHT, ICON_XS } from "@/constants";

import Page from "@/components/Page";
import ActionMenu from "@/components/Actions";
import ItemWrapper from "@/components/Wrapper/ItemWrapper";
import ItemPadding from "@/components/Wrapper/ItemPadding";
import NoItems from "@/components/ListItem/NoItems";
import ButtonWifiScan from "@/components/Button/ButtonWifiScan";

const SettingsNetwork = () => {
  const { networks, devices } = useSelector((state: any) => state.network);
  const { fetchDevices, handleDelete, handleDisconnect, handleConnectWifi } = useNetworkActions();

  useEffect(() => {
    fetchDevices();
  }, []);

  const ListTextItem = ({ title, desc }: { title: string; desc: string }) => {
    return (
      <div className="flex mt-2 text-neutral-500">
        <div className="w-40 flex dark:text-white text-black">{title}:</div>
        <div className="flex-1 flex flex-col">{desc}</div>
      </div>
    );
  };

  const getWifiIcon = (signal: number) => {
    if (signal > 75) return <WifiHighIcon weight={ICON_WEIGHT} size={ICON_SM} />;
    if (signal > 40) return <WifiMediumIcon weight={ICON_WEIGHT} size={ICON_SM} />;
    if (signal > 10) return <WifiLowIcon weight={ICON_WEIGHT} size={ICON_SM} />;
    return <WifiNoneIcon weight={ICON_WEIGHT} size={ICON_SM} />;
  };

  const ListWirelessNetwork = ({ network }: { network: WifiNetwork }) => {
    const actionItems = [
      {
        name: "Connect",
        icon: <WifiHighIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: () => handleConnectWifi(network),
        hide: network.connected,
      },
      {
        name: "Disconnect",
        icon: <WifiSlashIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: () => handleDisconnect("wlan0"),
        hide: !network.connected,
      },
      {
        name: "Forget Network",
        icon: <TrashSimpleIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: () => handleDelete(network.ssid),
        hide: !network.connected,
      },
    ];

    return (
      <div className="flex justify-between w-full">
        <div className="flex items-center">
          <div className="flex mr-2 items-center">{getWifiIcon(network.signal)}</div>

          <div className="text-lg font-medium">
            <div className="w-full">
              <div className={`${network.connected ? "text-yellow-700" : "dark:text-neutral-300 text-neutral-950"} flex `}>{network.ssid == ''? 'unknown' : network.ssid} </div>
              <div className="mb-1  text-neutral-500 text-left text-sm">{network.bssid}</div>
            </div>
          </div>
        </div>
        <div className="flex items-center">
          <div className="flex text-neutral-500 mr-1">{network.security ? <LockIcon weight={ICON_WEIGHT} size={ICON_SM} /> : ""}</div>
          <div className="-mr-2">
            <ActionMenu items={actionItems} />
          </div>
        </div>
      </div>
    );
  };

  const ListNetworkDevice = ({ ifname }: { ifname: string }) => {
    const actionItems = [
      {
        name: "Edit",
        icon: <PencilIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: () => undefined,
      },
    ];

    const [device, setDevice] = useState<NetworkDevice>({} as NetworkDevice);

    useEffect(() => {
      setDevice(devices[ifname]);
    }, [devices]);

    return (
      <div className="w-full">
        <div className="flex justify-between">
          <div className="font-medium">
            <div className="w-full flex">
              <div className="flex text-lg ">
                {device?.type === "wifi" ? (
                  <>
                    <WifiHighIcon weight={ICON_WEIGHT} size={ICON_SM} className="mr-2" />
                    Wifi
                  </>
                ) : device?.type === "ethernet" ? (
                  <>
                    <LaptopIcon weight={ICON_WEIGHT} size={ICON_SM} className="mr-2" />
                    Ethernet
                  </>
                ) : (
                  <>
                    <NetworkIcon weight={ICON_WEIGHT} size={ICON_SM} />
                    {device?.device}
                  </>
                )}
              </div>
            </div>
            <div className="mb-1  text-neutral-500 text-left">
              <ListTextItem desc={device?.connection} title="connection" />
            </div>
            <div className="mb-1  text-neutral-500 text-left">
              <ListTextItem desc={device?.mac_address} title="mac address" />
            </div>
            <div className="mb-1  text-neutral-500 text-left">
              <ListTextItem desc={device?.ipv4_address} title="ipv4 address" />
            </div>
            <div className="mb-1  text-neutral-500 text-left">
              <ListTextItem desc={device?.state} title="state" />
            </div>
          </div>
          <div className="-mr-2">
            <ActionMenu items={actionItems} />
          </div>
        </div>
      </div>
    );
  };

  return (
    <Page
      backButton
      title="Network"
      rightComponent={
        <div className="flex">
          <div className="mr-4">
            <ButtonWifiScan />
          </div>
        </div>
      }
    >
      <div className="md:flex">
        <ItemWrapper>
          <ItemPadding>
            <ListNetworkDevice ifname="wlan0" />
          </ItemPadding>
        </ItemWrapper>

        <ItemWrapper>
          <ItemPadding>
            <ListNetworkDevice ifname="eth0" />
          </ItemPadding>
        </ItemWrapper>
      </div>

      <div className="p-4">
        <h2 className="mt-3 text-xl">Available Networks</h2>
      </div>
      {networks.length ? (
        networks.map((network: WifiNetwork, index: number) => (
          <ItemWrapper key={index}>
            <ItemPadding>
              <ListWirelessNetwork network={network} />
            </ItemPadding>
          </ItemWrapper>
        ))
      ) : (
        <NoItems
          title="No Networks Found"
          desc={"Scan to search for available wireless networks"}
          icon={<WifiHighIcon weight={ICON_WEIGHT} size={ICON_SM} />}
        />
      )}
    </Page>
  );
};

export default SettingsNetwork;
