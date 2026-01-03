import { ReactElement, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { useSourceService } from "@/services/source";
import { ICON_LG, ICON_WEIGHT } from "@/constants";
import { DIALOG_EVENTS, OVERLAY_EVENTS } from "@/store/constants";
import {
  AirplayIcon,
  BluetoothIcon,
  GearIcon,
  GlobeHemisphereWestIcon,
  HardDrivesIcon,
  PlaylistIcon,
  SpeakerHifiIcon,
  SpotifyLogoIcon,
  VinylRecordIcon,
} from "@phosphor-icons/react";
import { Swiper, SwiperSlide } from "swiper/react";
import {
  FreeMode,
  Keyboard,
  Mousewheel,
  Pagination,
  Scrollbar,
} from "swiper/modules";
import '../../../node_modules/swiper/swiper.css';
import '../../../node_modules/swiper/modules/free-mode.css';
import '../../../node_modules/swiper/modules/pagination.css';

import ButtonStandby from "@/components/Button/ButtonStandby";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import Spinner from "@/components/Spinner";
import Page from "@/components/Page";

type SourceItem = {
  name: string;
  icon: ReactElement;
  alias: string;
  url?: string;
  disabled?: boolean;
  render?: boolean;
  type?: string;
};
const sources: SourceItem[] = [
  {
    name: "Playlists",
    icon: <PlaylistIcon weight={ICON_WEIGHT} size={ICON_LG} />,
    alias: "playlist",
  },
  {
    name: "Library",
    icon: <VinylRecordIcon weight={ICON_WEIGHT} size={ICON_LG} />,
    alias: "library",
  },
  {
    name: "Storage",
    icon: <HardDrivesIcon weight={ICON_WEIGHT} size={ICON_LG} />,
    alias: "storage",
  },
  {
    name: "Radio",
    icon: <GlobeHemisphereWestIcon weight={ICON_WEIGHT} size={ICON_LG} />,
    alias: "radio",
  },
  {
    name: "Bluetooth",
    icon: <BluetoothIcon weight={ICON_WEIGHT} size={ICON_LG} />,
    alias: "bluetooth",
  },
  {
    name: "Spotify",
    icon: <SpotifyLogoIcon weight={ICON_WEIGHT} size={ICON_LG} />,
    alias: "spotify",
  },
  {
    name: "Airplay",
    icon: <AirplayIcon weight={ICON_WEIGHT} size={ICON_LG} />,
    alias: "shairportsync",
  },
  {
    name: "Multiroom",
    icon: <SpeakerHifiIcon weight={ICON_WEIGHT} size={ICON_LG} />,
    alias: "snapcast",
  },
  {
    name: "Settings",
    icon: <GearIcon weight={ICON_WEIGHT} size={ICON_LG} />,
    alias: "settings",
  },
];

const Start = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const { setSource } = useSourceService();
  const { source } = useSelector((state: any) => state.player);
  const { adapter_state } = useSelector((state: any) => state.bluetooth);

  const [isLoading, setIsLoading] = useState<string>("");

  const onClickHandler = async (item: SourceItem) => {
    setIsLoading(item.alias);
    if (["bluetooth", "spotify", "shairportsync"].includes(item.alias)) {
      if (await setSource(item.alias)) {
        dispatch({ type: OVERLAY_EVENTS.OVERLAY_NOWPLAYING });

        if (item.alias === "bluetooth" && !adapter_state.connected) {
          dispatch({ type: DIALOG_EVENTS.DIALOG_BLUETOOTH_NOT_CONNECTED });
        }
      }
    } else {
      navigate(`/${item.alias}`);
    }
    setIsLoading("");
  };

  return (
    <Page title="Start" rightComponent={ 
      <div className="flex h-[50px] items-center mr-4">
        <ButtonStandby/>
      </div>
    }>
      <LayoutHeightWrapper>
        <div className="px-4 flex items-center h-full">
          <div className="w-full">
            <Swiper
              modules={[FreeMode, Keyboard, Mousewheel, Pagination, Scrollbar]}
              spaceBetween={10}
              slidesPerView={3}
              freeMode={true}
              resistance={false}
              touchReleaseOnEdges={true}
              grabCursor={true}
              direction={"horizontal"}
              mousewheel={true}
              pagination={{
                el: ".custom-pagination",
                clickable: true,
              }}
              breakpoints={{
                640: {
                  slidesPerView: 4,
                },
                768: {
                  slidesPerView: 5,
                },
                1024: {
                  slidesPerView: 5,
                },
                1280: {
                  slidesPerView: 5,
                },
              }}
              keyboard={{
                enabled: true,
              }}
            >
              {sources.map((item) => (
                <SwiperSlide>
                  <button
                    key={item.alias}
                    disabled={item.disabled}
                    onClick={() => onClickHandler(item)}
                    className={`grayscale-40 touch-pan-x bg-neutral-900 dark:bg-neutral-950 rounded-sm  text-white  flex items-center justify-center aspect-square overflow-hidden w-full mr-2
                bg-radial-[at_15%_5%]  cursor-pointer ${item.disabled ? "opacity-30 from-neutral-500 to-neutral-950" :  source.type === item.alias
                    ? "from-yellow-950 to-yellow-950"
                    : "from-yellow-700 to-yellow-950 hover:from-yellow-800 "}`}
                  >
                    <div className="flex flex-col items-center">
                      <div className="mb-2">
                        {isLoading === item.alias ? <Spinner /> : item.icon}
                      </div>
                      <div>{item.name}</div>
                    </div>
                  </button>
                </SwiperSlide>
              ))}
            </Swiper>

            <div className="custom-pagination flex gap-2 items-center justify-center mt-4"></div>
          </div>
        </div>
        </LayoutHeightWrapper>
    </Page>
  );
};

export default Start;
