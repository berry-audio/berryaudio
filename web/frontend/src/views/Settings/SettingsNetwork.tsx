import Page from "@/components/Page";
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
import { useDispatch, useSelector } from "react-redux";
import { useEffect, useState } from "react";
import { NetworkDevice, WifiNetwork } from "@/types";
import { useNetworkService } from "@/services/network";
import { ICON_SM, ICON_WEIGHT, ICON_XS } from "@/constants";
import { DIALOG_EVENTS, INFO_EVENTS, OVERLAY_EVENTS } from "@/store/constants";

import ActionMenu from "@/components/Actions";
import ItemWrapper from "@/components/Wrapper/ItemWrapper";
import ItemPadding from "@/components/Wrapper/ItemPadding";
import Spinner from "@/components/Spinner";
import ButtonBluetoothToggle from "@/components/Button/ButtonBluetoothToggle";
import NoItems from "@/components/ListItem/NoItems";
import ButtonWifiScan from "@/components/Button/ButtonWifiScan";

const SettingsNetwork = () => {
  const dispatch = useDispatch();
  const { networks } = useSelector((state: any) => state.network);
  const { getDevice } = useNetworkService();

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
        action: () => undefined,
      },
      {
        name: "Disconnect",
        icon: <WifiSlashIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: async () => undefined,
      },
      {
        name: "Forget Network",
        icon: <TrashSimpleIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: async () => undefined,
      },,
    ];

    return (
      <div className="flex justify-between w-full -my-2">
        <div className="flex items-center">
          <div className="flex mr-2 items-center">{getWifiIcon(network.signal)}</div>
          <div className={`${network.connected ? "text-yellow-700" : "dark:text-neutral-300 text-neutral-950"} flex `}>{network.ssid} </div>
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

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [device, setDevice] = useState<NetworkDevice>({} as NetworkDevice);

    useEffect(() => {
      (async () => {
        setIsLoading(true);
        const _res = await getDevice(ifname);
        setDevice(_res);
        setIsLoading(false);
      })();
    }, []);

    return (
      <>
        {isLoading ? (
          <div className="flex justify-center items-center w-full">
            <Spinner />
          </div>
        ) : (
          <div className="w-full">
            <div className="flex justify-between">
              <div className="font-medium">
                <div className="w-full flex">
                  <div className="flex text-lg ">
                    {device.type === "wifi" ? (
                      <>
                        <WifiHighIcon weight={ICON_WEIGHT} size={ICON_SM} className="mr-2" />
                        Wifi
                      </>
                    ) : device.type === "ethernet" ? (
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
              </div>
              <div className="-mr-2">
                <ActionMenu items={actionItems} />
              </div>
            </div>
          </div>
        )}
      </>
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
          <div className="mr-4">
            <ButtonBluetoothToggle />
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
