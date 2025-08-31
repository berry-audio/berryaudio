import { useEffect, useState } from "react";
import { Select } from "antd";
import { useMixerService } from "@/services/mixer";
import { CustomSelect, PcmDevice, SelectOption } from "@/types";

/**
 * Select component for PCM audio devices.
 *
 * @template T - Type of the selected value.
 * @param {T} value - Current value.
 * @param {(value: T) => void} onChange - Called on value change.
 * @param {import('antd').SelectProps<T>} [rest] - Other Select props.
 */
const SelectPcmDevices = ({ value, onChange, ...rest }: CustomSelect) => {
  const { getPlaybackDevices } = useMixerService();

  const [pcmDevices, setPcmDevices] = useState<SelectOption[]>([]);

  const fetchPlaybackDevices = async () => {
    const res = await getPlaybackDevices();

    function _convertAplayDevices(devices: PcmDevice[]) {
      return devices?.map((device) => ({
        label: device.device,
        value: device.device,
      }));
    }

    setPcmDevices(_convertAplayDevices(res));
  };

  useEffect(() => {
    fetchPlaybackDevices();
  }, []);

  return (
    <Select
      placeholder="Available devices"
      optionFilterProp="label"
      options={pcmDevices}
      size="large"
      value={value}
      onChange={onChange}
      {...rest}
    />
  );
};

export default SelectPcmDevices;
