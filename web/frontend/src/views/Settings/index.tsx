import { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { BluetoothIcon, CpuIcon, GearIcon, InfoIcon, NetworkIcon, SpeakerHifiIcon, StackIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import Page from "@/components/Page";
import ListMenu from "@/components/ListMenu";

export interface SettingsItem {
  name: string;
  alias: string;
  icon: ReactNode;
  url: string;
  disabled?: boolean;
}

const SettingsItems: SettingsItem[] = [
  {
    name: "General",
    alias: "general",
    icon: <GearIcon weight={ICON_WEIGHT} size={ICON_SM} />,
    url: "/settings/general",
  },
  {
    name: "Library",
    alias: "library",
    icon: <StackIcon weight={ICON_WEIGHT} size={ICON_SM} />,
    url: "/settings/library",
  },
  {
    name: "Bluetooth",
    alias: "bluetooth",
    icon: <BluetoothIcon weight={ICON_WEIGHT} size={ICON_SM} />,
    url: "/settings/bluetooth",
  },
  {
    name: "Network",
    alias: "network",
    icon: <NetworkIcon weight={ICON_WEIGHT} size={ICON_SM} />,
    url: "/settings/network",
  },
  {
    name: "Camilla DSP",
    alias: "camilladsp",
    icon: <CpuIcon weight={ICON_WEIGHT} size={ICON_SM} />,
    url: "/settings/dsp",
  },

  {
    name: "Multiroom",
    alias: "multiroom",
    icon: <SpeakerHifiIcon weight={ICON_WEIGHT} size={ICON_SM} />,
    url: "/settings/snapcast",
  },
  {
    name: "About",
    alias: "about",
    icon: <InfoIcon weight={ICON_WEIGHT} size={ICON_SM} />,
    url: "/settings/about",
  },
];

const Settings = () => {
  const navigate = useNavigate();

  const onClickHandler = async (source: any) => {
    if (source.url) navigate(source.url);
  };

  return (
    <Page backButton title="Settings">
      {SettingsItems.map((source: SettingsItem, index: number) => (
        <ListMenu key={index} name={source.name} icon={source.icon} onClick={() => onClickHandler(source)} disabled={source?.disabled} />
      ))}
    </Page>
  );
};

export default Settings;
