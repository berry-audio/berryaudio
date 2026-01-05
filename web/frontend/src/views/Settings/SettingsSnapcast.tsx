import { useSelector } from "react-redux";
import { useEffect } from "react";
import { useSnapcastService } from "@/services/snapcast";
import { useSnapcastActions } from "@/hooks/useSnapcastActions";
import { SnapcastServer } from "@/types";
import { SpeakerHifiIcon, SpeakerHighIcon, SpeakerSimpleXIcon } from "@phosphor-icons/react";
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
  const { servers } = useSelector((state: any) => state.snapcast);

  const { connect, disconnect } = useSnapcastService();
  const { fetchServers, loading } = useSnapcastActions();

  useEffect(() => {
    fetchServers();
  }, []);

  const ListItem = ({ item }: { item: SnapcastServer }) => {
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
                  <ListItem item={item} />
                </ItemPadding>
              </ItemWrapper>
            ))
          ) : (
            <LayoutHeightWrapper>
              <NoItems
                title="No Servers Found"
                desc={"Scan to search for available servers"}
                icon={<SpeakerHifiIcon weight={ICON_WEIGHT} size={ICON_SM} />}
              />
            </LayoutHeightWrapper>
          )}
        </>
      )}
    </Page>
  );
};

export default SettingsSnapcast;
