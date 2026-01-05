import { JSX } from "react";
import { useSelector } from "react-redux";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import {
  AirplayIcon,
  BluetoothIcon,
  SpeakerHifiIcon,
  SpotifyLogoIcon,
} from "@phosphor-icons/react";

const Source = ({
  className,
  hideText,
  hideIcon = false,
}: {
  className?: string;
  hideText?: boolean;
  hideIcon?: boolean;
}) => {
  const { source } = useSelector((state: any) => state.player);
  const source_name = source.state?.name === 'none' ? "" : source.state?.name

  const sourceIcon: Record<string, JSX.Element | null> = {
    local: null,
    spotify: <SpotifyLogoIcon weight={ICON_WEIGHT} size={ICON_SM} />,
    shairportsync: <AirplayIcon weight={ICON_WEIGHT} size={ICON_SM} />,
    bluetooth: <BluetoothIcon weight={ICON_WEIGHT} size={ICON_SM} />,
    snapcast: <SpeakerHifiIcon weight={ICON_WEIGHT} size={ICON_SM} />
  };

  return (
    source?.state?.connected && (
      <div className={`flex items-center ${className}`}>
        {!hideIcon && (
          <div
            className={`cursor-pointer flex items-center relative rounded-full ${
              !hideText && "mr-2"
            }`}
          >
            {sourceIcon[source.type]}
          </div>
        )}

        {!hideText && <div>{source_name}</div>}
      </div>
    )
  );
};

export default Source;
