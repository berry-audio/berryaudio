import { useEffect, useState } from "react";
import { useMixerService } from "@/services/mixer";
import { PcmDevice } from "@/types";

import SelectComboBox from "./SelectComboBox";

interface SelectPcmDevicesProps {
  value?: string | null;
  onChange: (value: string | null) => void;
  placeholder?: string;
}

function SelectPcmDevices({ ...props }: SelectPcmDevicesProps) {
  const { getPlaybackDevices } = useMixerService();
  const [pcmDevices, setPcmDevices] = useState<PcmDevice[]>([]);

  useEffect(() => {
    const fetchPlaybackDevices = async () => {
      const response = await getPlaybackDevices();
      setPcmDevices(response);
    };
    fetchPlaybackDevices();
  }, []);

  const items = pcmDevices.map((device) => ({
    label: device.card_name,
    value: device.device,
    description: device.device,
  }));
  return <SelectComboBox items={items} {...props} />;
}

export default SelectPcmDevices;
