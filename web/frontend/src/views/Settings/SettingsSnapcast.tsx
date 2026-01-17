import { shallowEqual, useDispatch, useSelector } from "react-redux";
import { useEffect, useState } from "react";
import { useSnapcastService } from "@/services/snapcast";
import { useSnapcastActions } from "@/hooks/useSnapcastActions";
import { SnapcastServer } from "@/types";
import { Slider } from "@/components/Form/Slider";
import {
  DeviceMobileSpeakerIcon,
  HardDriveIcon,
  SpeakerHifiIcon,
  SpeakerHighIcon,
  SpeakerSimpleXIcon,
  SpeakerSlashIcon,
  WarningCircleIcon,
} from "@phosphor-icons/react";
import { EVENTS } from "@/constants/events";
import { INFO_EVENTS } from "@/store/constants";
import { ICON_SM, ICON_WEIGHT, ICON_XS } from "@/constants";

import Page from "@/components/Page";
import ActionMenu from "@/components/Actions";
import ItemWrapper from "@/components/Wrapper/ItemWrapper";
import ItemPadding from "@/components/Wrapper/ItemPadding";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import Spinner from "@/components/Spinner";
import NoItems from "@/components/ListItem/NoItems";
import ButtonSnapcastScan from "@/components/Button/ButtonSnapcastScan";
import ButtonIcon from "@/components/Button/ButtonIcon";
import ButtonSnapcastInfo from "@/components/Button/ButtonSnapcastInfo";

const SettingsSnapcast = () => {
  const connected = useSelector((state: any) => state.socket.connected);
  const { servers, status } = useSelector((state: any) => state.snapcast, shallowEqual);

  const { connect, disconnect, setVolume } = useSnapcastService();
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
          return <SpeakerHighIcon size={ICON_XS} weight={ICON_WEIGHT} className="ml-2 text-primary" />;
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
            <HardDriveIcon size={ICON_SM} weight={ICON_WEIGHT} className={`mr-3 ${item?.connected ? "text-primary" : ""}`} />
            <div className="text-lg font-medium">
              <div className="w-full">
                <div className="flex items-center">
                  {item?.name} <RenderStatus />
                </div>
                <div className="mb-1  text-secondary text-left">{item?.ip}</div>
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
    const dispatch = useDispatch();
    const { id, config } = item;
    const { percent, muted } = config?.volume;

    const [volumeLevel, setvolumeLevel] = useState<any>(percent);

    const commitVolume = async (volume: number, muted?: boolean) => {
      try {
        dispatch({ type: INFO_EVENTS.SNAPCAST_VOLUME_DRAGGING, payload: false });
        dispatch({
          type: EVENTS.SNAPCAST_NOTIFICATION,
          payload: {
            method: "Client.OnVolumeChanged",
            params: {
              id,
              volume: {
                percent: volume,
                muted: muted,
              },
            },
          },
        });
      } catch (error) {
        throw error;
      }
    };

    const onClickToggleMuteHandler = async () => {
      await setVolume(id, percent, !muted);
    };

    const onCommittedVolume = async ([value]: number[]) => {
      await commitVolume(value);
    };

    const onChangeVolume = ([value]: number[]) => {
      dispatch({ type: INFO_EVENTS.SNAPCAST_VOLUME_DRAGGING, payload: true });
      setvolumeLevel(value);
      setVolume(id, value);
    };

    const onMouseEnter = () => {
      dispatch({ type: INFO_EVENTS.SNAPCAST_VOLUME_DRAGGING, payload: true });
    };

    const onMouseLeave = () => {
      dispatch({ type: INFO_EVENTS.SNAPCAST_VOLUME_DRAGGING, payload: false });
    };

    useEffect(() => {
      setvolumeLevel(percent);
    }, [percent]);

    return (
      <div className="w-full">
        <div className="flex items-center">
          <SpeakerHifiIcon size={ICON_SM} weight={ICON_WEIGHT} className={`mr-3 ${item?.connected ? "text-primary" : ""}`} />
          <div className="font-medium flex-1">
            <div>{item?.host?.name}</div>
            <div className="mb-1  text-secondary text-left">{item?.host?.os}</div>
          </div>
        </div>
        <div className="flex">
          <div className="mr-2">
            <ButtonIcon onClick={() => onClickToggleMuteHandler()}>
              {muted ? (
                <SpeakerSlashIcon size={ICON_SM} weight={ICON_WEIGHT} className="text-muted" />
              ) : (
                <SpeakerHighIcon size={ICON_SM} weight={ICON_WEIGHT} />
              )}
            </ButtonIcon>
          </div>
          <Slider
            value={[volumeLevel]}
            max={100}
            step={1}
            className="w-full md:w-80 rounded-full volume-slider"
            onValueChange={onChangeVolume}
            onValueCommit={onCommittedVolume}
            onMouseLeave={onMouseLeave}
            onPointerLeave={onMouseLeave}
            onMouseEnter={onMouseEnter}
            disabled={false}
          />
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
            <ButtonSnapcastInfo />
          </div>
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
              <h2 className="mt-2 font-medium">No Servers Found</h2>
              <p className="mb-4 w-80 text-secondary">Scan for available servers on the network</p>
            </div>
          )}

          <div className="p-4">
            <h2 className="mt-3 text-xl">Players</h2>
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
