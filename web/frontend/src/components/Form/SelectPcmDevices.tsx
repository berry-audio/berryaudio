import { useEffect, useState } from "react";
import { useMixerService } from "@/services/mixer";
import { PcmDevice } from "@/types";

import SelectComboBox from "./SelectComboBox";

function SelectPcmDevices({ onChange, initialValue }: any) {
  const { getPlaybackDevices } = useMixerService();

  const [pcmDevices, setPcmDevices] = useState<PcmDevice[]>([]);

  const fetchPlaybackDevices = async () => {
    const response = await getPlaybackDevices();
    setPcmDevices(response);
  };

  useEffect(() => {
    fetchPlaybackDevices();
  }, []);

  return (
    <SelectComboBox
      items={pcmDevices?.map((device) => ({
        label: device.card_name,
        value: device.device,
        description: device.device,
      }))}
      initialValue={initialValue}
      onChange={onChange}
      placeholder="Select device"
    />
  );
}

export default SelectPcmDevices;
