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

  const items = pcmDevices?.map((device) => ({
    label: device.name,
    value: device.device,
    description: device.description,
  }));

  const hasCurrentValue = pcmDevices?.some((device: PcmDevice) => device.device === props.value);

  if (!hasCurrentValue) {
    props.value = null;
  }

  return <SelectComboBox items={items} {...props} />;
}

export default SelectPcmDevices;
