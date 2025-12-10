import Page from "@/components/Page";
import {
  BluetoothIcon,
  BluetoothSlashIcon,
  DeviceMobileIcon,
  HeadphonesIcon,
  LaptopIcon,
  TrashSimpleIcon,
} from "@phosphor-icons/react";
import { useBluetoothService } from "@/services/bluetooth";
import { useDispatch, useSelector } from "react-redux";
import { useEffect, useState } from "react";
import { BluetoothDevice } from "@/types";
import { BluetoothConnectedIcon } from "@phosphor-icons/react/dist/ssr";
import { ICON_SM, ICON_WEIGHT, ICON_XS } from "@/constants";
import { DIALOG_EVENTS, INFO_EVENTS, OVERLAY_EVENTS } from "@/store/constants";

import ActionMenu from "@/components/Actions";
import ItemWrapper from "@/components/Wrapper/ItemWrapper";
import ItemPadding from "@/components/Wrapper/ItemPadding";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import Spinner from "@/components/Spinner";
import ButtonBluetoothScan from "@/components/Button/ButtonBluetoothScan";
import ButtonBluetoothToggle from "@/components/Button/ButtonBluetoothToggle";
import NoItems from "@/components/ListItem/NoItems";

const SettingsBluetooth = () => {
  const dispatch = useDispatch();
  const { devices_available } = useSelector(
    (state: any) => state.bluetooth
  );
  const { getDevices, removeDevice, disconnectDevice, connectDevice } =
    useBluetoothService();

  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchDevices = async () => {
    setIsLoading(true);
    const res = await getDevices();
    dispatch({
      type: INFO_EVENTS.BLUETOOTH_SCAN_COMPLETED,
      payload: res,
    });
    setIsLoading(false);
  };

  useEffect(() => {
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
    dispatch({ type: OVERLAY_EVENTS.OVERLAY_CLOSE });
    fetchDevices();
  }, []);

  const ListItem = ({ item }: { item: BluetoothDevice }) => {
    const actionItems = [
      {
        name: "Connect",
        icon: <BluetoothConnectedIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: () => connectDevice(item.path),
        hide: item.connected,
      },
      {
        name: "Disconnect",
        icon: <BluetoothSlashIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: async () => disconnectDevice(item.path),
        hide: !item.connected,
      },
      {
        name: "Forget",
        icon: <TrashSimpleIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: async () => removeDevice(item.path),
      },
    ];

    const RenderIcon = ({
      type,
      className,
    }: {
      type: string;
      className: string;
    }) => {
      switch (type) {
        case "audio-headset":
          return (
            <HeadphonesIcon
              weight={ICON_WEIGHT}
              size={ICON_SM}
              className={className}
            />
          );
        case "phone":
          return (
            <DeviceMobileIcon
              weight={ICON_WEIGHT}
              size={ICON_SM}
              className={className}
            />
          );
        case "computer":
          return (
            <LaptopIcon
              weight={ICON_WEIGHT}
              size={ICON_SM}
              className={className}
            />
          );
        default:
          return (
            <BluetoothIcon
              weight={ICON_WEIGHT}
              size={ICON_SM}
              className={className}
            />
          );
      }
    };

    return (
      <div className="w-full">
        <div className="flex justify-between items-center">
          <div className="flex  items-center">
            <RenderIcon
              type={item.icon}
              className={`mr-2 ${item.connected ? "text-yellow-700" : ""}`}
            />
            <div className="text-lg font-medium">
              <div className="w-full">
                <div>{item.name}</div>
                <div className="mb-1  text-neutral-500 text-left text-sm">
                  {item.address}
                </div>
              </div>
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
      title="Bluetooth"
      rightComponent={
        <div className="flex">
          <div className="mr-4">
            <ButtonBluetoothScan />
          </div>
          <div className="mr-4">
            <ButtonBluetoothToggle />
          </div>
        </div>
      }
    >
      {isLoading ? (
        <LayoutHeightWrapper>
          <Spinner />
        </LayoutHeightWrapper>
      ) : (
        <>
          {devices_available.length ? (
            devices_available.map((item: BluetoothDevice, index: number) => (
              <ItemWrapper key={index}>
                <ItemPadding>
                  <ListItem item={item} />
                </ItemPadding>
              </ItemWrapper>
            ))
          ) : (
            <LayoutHeightWrapper>
              <NoItems
                title="No Devices Found"
                desc={"Scan to search for available devices"}
                icon={<BluetoothIcon weight={ICON_WEIGHT} size={ICON_SM} />}
              />
            </LayoutHeightWrapper>
          )}
        </>
      )}
    </Page>
  );
};

export default SettingsBluetooth;
