import Page from "@/components/Page";
import { MusicNoteSimpleIcon, SpeakerHifiIcon, SpeakerHighIcon, SpeakerNoneIcon, SpeakerSimpleSlashIcon, SpeakerSimpleXIcon, SpeakerXIcon } from "@phosphor-icons/react";
import { useDispatch, useSelector } from "react-redux";
import { useEffect, useState } from "react";
import { useSnapcastService } from "@/services/snapcast";
import { SnapcastServer } from "@/types";
import { ICON_SM, ICON_WEIGHT, ICON_XS } from "@/constants";
import { DIALOG_EVENTS, OVERLAY_EVENTS } from "@/store/constants";

import ActionMenu from "@/components/Actions";
import ItemWrapper from "@/components/Wrapper/ItemWrapper";
import ItemPadding from "@/components/Wrapper/ItemPadding";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import Spinner from "@/components/Spinner";

import NoItems from "@/components/ListItem/NoItems";
import ButtonSnapcastScan from "@/components/Button/ButtonSnapcastScan";

const SettingsSnapcast = () => {
  const dispatch = useDispatch();
  const { servers_available } = useSelector((state: any) => state.snapcast);
  const { connect, disconnect } = useSnapcastService();

  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    dispatch({ type: DIALOG_EVENTS.DIALOG_CLOSE });
    dispatch({ type: OVERLAY_EVENTS.OVERLAY_CLOSE });
  }, []);

  const ListItem = ({ item }: { item: SnapcastServer }) => {
    const actionItems = [
      {
        name: "Connect",
        icon: <SpeakerHighIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: () => connect(item.ip),
        hide: item.connected,
      },
      {
        name: "Disconnect",
        icon: <SpeakerSimpleXIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: async () => disconnect(),
        hide: !item.connected,
      },
    ];

    const RenderStatus = () => {
      switch (item.status) {
        case "idle":
          return <SpeakerNoneIcon size={ICON_XS} weight={ICON_WEIGHT} className="ml-2 " />;
        case "playing":
          return <SpeakerHighIcon size={ICON_XS} weight={ICON_WEIGHT} className="ml-2 " />;
        default:
          return <SpeakerSimpleSlashIcon size={ICON_XS} weight={ICON_WEIGHT} className="ml-2 text-neutral-500" />;
      }
    };

    return (
      <div className="w-full" >
        <div className="flex justify-between items-center">
          <div className="flex items-center" onClick={()=>connect(item.ip)}>
            <SpeakerHifiIcon size={ICON_SM} weight={ICON_WEIGHT} className={`mr-3 ${item.connected ? "text-yellow-700" : ""}`} />
            <div className="text-lg font-medium">
              <div className="w-full">
                <div className="flex items-center">
                  {item.hostname} <RenderStatus />
                </div>
                <div className="mb-1  text-neutral-500 text-left text-sm">{item.ip}</div>
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
      {isLoading ? (
        <LayoutHeightWrapper>
          <Spinner />
        </LayoutHeightWrapper>
      ) : (
        <>
          {servers_available.length ? (
            servers_available.map((item: SnapcastServer, index: number) => (
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
