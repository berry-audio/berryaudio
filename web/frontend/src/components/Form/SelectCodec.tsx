import SelectComboBox from "./SelectComboBox";

interface SelectTimezoneProps {
  value?: string;
  placeholder?: string;
  onChange: (value: string | null) => void;
}

const SelectCodec = ({ ...props }: SelectTimezoneProps) => {
  const codecOptions = [
    { value: "pcm", label: "PCM" },
    { value: "flac", label: "FLAC" },
    { value: "opus", label: "Opus" },
    { value: "ogg", label: "Ogg" },
  ];

  return <SelectComboBox items={codecOptions.map((codec) => ({ ...codec }))} {...props} />;
};

export default SelectCodec;
