import { useSelector } from "react-redux";
import { useEffect } from "react";
import { useSnapcastService } from "@/services/snapcast";
import { useSnapcastActions } from "@/hooks/useSnapcastActions";
import { SnapcastServer } from "@/types";
import { DeviceMobileSpeakerIcon, SpeakerHifiIcon, SpeakerHighIcon, SpeakerSimpleXIcon, WarningCircleIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT, ICON_XS } from "@/constants";

import Page from "@/components/Page";
import ActionMenu from "@/components/Actions";
import ItemWrapper from "@/components/Wrapper/ItemWrapper";
import ItemPadding from "@/components/Wrapper/ItemPadding";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import Spinner from "@/components/Spinner";
import NoItems from "@/components/ListItem/NoItems";
import ButtonSnapcastScan from "@/components/Button/ButtonSnapcastScan";

const SettingsSnapcast = () => {
  const connected = useSelector((state: any) => state.socket.connected);
  const { servers, status } = useSelector((state: any) => state.snapcast);

  const { connect, disconnect } = useSnapcastService();
  const { fetchServers, getServerStatus, loading } = useSnapcastActions();

  useEffect(() => {
    if (!connected) return;

    fetchServers();
    getServerStatus();
  }, [connected]);

  const ListServer = ({ item }: { item: SnapcastServer }) => {
    const actionItems = [
      {
        name: "Connect",
        icon: <SpeakerHighIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: () => connect(item.ip),
        hide: item?.connected,
      },
      {
        name: "Disconnect",
        icon: <SpeakerSimpleXIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: async () => disconnect(),
        hide: !item?.connected,
      },
    ];

    const RenderStatus = () => {
      switch (item?.status) {
        case "idle":
          return "";
        case "playing":
          return <SpeakerHighIcon size={ICON_XS} weight={ICON_WEIGHT} className="ml-2 text-yellow-700" />;
        case "unavailable":
          return <WarningCircleIcon size={ICON_XS} weight={ICON_WEIGHT} className="ml-2 text-red-400" />;
      default:
          return "";
      }
    };

    return (
      <div className="w-full">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <SpeakerHifiIcon size={ICON_SM} weight={ICON_WEIGHT} className={`mr-3 ${item?.connected ? "text-yellow-700" : ""}`} />
            <div className="text-lg font-medium">
              <div className="w-full">
                <div className="flex items-center">
                  {item?.name} <RenderStatus />
                </div>
                <div className="mb-1  text-neutral-500 text-left text-sm">{item?.ip}</div>
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

  const ListClient = ({ item }: { item: any }) => {
    return (
      <div className="w-full">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <DeviceMobileSpeakerIcon size={ICON_SM} weight={ICON_WEIGHT} className={`mr-3 ${item?.connected ? "text-yellow-700" : ""}`} />
            <div className="text-lg font-medium">
              <div className="w-full">
                <div className="flex items-center">{item?.host?.name} {item?.config?.volume?.percent} {item?.config?.volume?.muted ? 'mute' : 'unmuted'}</div>
                <div className="mb-1  text-neutral-500 text-left text-sm">{item?.host?.os}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Page
      backButton
      title="Multiroom"
      rightComponent={
        <div className="flex">
          <div className="mr-4">
            <ButtonSnapcastScan />
          </div>
        </div>
      }
    >
      {loading ? (
        <LayoutHeightWrapper>
          <Spinner />
        </LayoutHeightWrapper>
      ) : (
        <>
          {servers.length ? (
            servers.map((item: SnapcastServer, index: number) => (
              <ItemWrapper key={index}>
                <ItemPadding>
                  <ListServer item={item} />
                </ItemPadding>
              </ItemWrapper>
            ))
          ) : (
            <div className="flex w-full flex-col items-center justify-center text-center">
              <SpeakerHifiIcon weight={ICON_WEIGHT} size={ICON_SM} />
              <h2 className="mt-2 text-lg">No Servers Found</h2>
              <p className="mb-4 text-sm w-80 text-neutral-950/50 dark:text-neutral-50/50">Scan to search for available servers on the network</p>
            </div>
          )}

          <div className="p-4">
            <h2 className="mt-3 text-xl">Clients</h2>
          </div>
          {status?.groups?.length ? (
            status.groups.map((group: any) =>
              group?.clients?.map((client: any, index: number) => (
                <ItemWrapper key={index}>
                  <ItemPadding>
                    <ListClient item={client} />
                  </ItemPadding>
                </ItemWrapper>
              ))
            )
          ) : (
            <NoItems
              title="No Clients Found"
              desc="Connect to a server to see list of available clients"
              icon={<DeviceMobileSpeakerIcon weight={ICON_WEIGHT} size={ICON_SM} />}
            />
          )}
        </>
      )}
    </Page>
  );
};

export default SettingsSnapcast;
