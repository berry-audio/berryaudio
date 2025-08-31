import { useSelector } from "react-redux";
import { PlugsIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import NoItems from "../ListItem/NoItems";
import Overlay from ".";

const OverlayOffline = () => {
  const connected = useSelector((state: any) => state.socket.connected);
  
  return (
    <Overlay zindex={100} show={!connected} overlay>
      <NoItems
        title={"Device Offline"}
        desc={
          <span className="text-white/50">
            Backend is not running please unplug and replug the
            device
          </span>
        }
        icon={
          <PlugsIcon
            className="text-yellow-700"
            weight={ICON_WEIGHT}
            size={ICON_SM}
          />
        }
      />
    </Overlay>
  );
};

export default OverlayOffline;
