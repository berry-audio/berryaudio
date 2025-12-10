import React from "react";

const Toggle = ({
  label = "",
  onLabel = "On",
  offLabel = "Off",
  className = "",
  onValueChange,
  defaultValue = false,
}: {
  label?: string;
  onLabel?: string;
  offLabel?: string;
  className?: string;
  onValueChange?: (value: boolean) => void;
  defaultValue?: boolean;
}) => {
  const [isChecked, setIsChecked] = React.useState<boolean>(defaultValue);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIsChecked(e.target.checked);
    if (onValueChange) {
      onValueChange(e.target.checked);
    }
  };

  return (
    <label className={`cursor-pointer ${className} block`}>
      <div className="mb-2">{label}</div>
      <div className="inline-flex">
        <input type="checkbox" value="1" className="sr-only peer" onChange={handleChange} checked={isChecked} />
        <div
          className={`relative w-11 h-6 ${
            isChecked ? "bg-yellow-700" : "bg-neutral-500/30"
          } peer-focus:outline-none  peer-focus:ring-brand-soft dark:peer-focus:ring-brand-soft rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-buffer after:content-[''] after:absolute after:top-0.5 after:start-0.5 after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand`}
        ></div>
        <span className="select-none ms-3 text-sm font-medium text-heading">{isChecked ? onLabel : offLabel}</span>
      </div>
    </label>
  );
};

export default Toggle;
