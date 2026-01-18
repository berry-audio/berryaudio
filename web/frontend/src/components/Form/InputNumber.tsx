import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export interface InputNumberProps {
  value: number;
  min?: number;
  max?: number;
  onChange: (value: number) => void;
}

const step = 1;

export function InputNumber({ value, min = 1, max = 10000, onChange }: InputNumberProps) {
  const updateValue = (newValue: number) => {
    const clamped = Math.min(Math.max(newValue, min), max);
    onChange(clamped);
  };

  return (
    <div className="flex flex-col space-y-2 w-40">
      <div className="flex">
        <Button type="button" onClick={() => updateValue(value - step)} className="rounded-r-none bg-popover h-full px-3 ">
          −
        </Button>
        <Input
          type="number"
          value={value}
          onChange={(e) => {
            const val = Number(e.target.value);
            if (!isNaN(val)) updateValue(val);
          }}
          className="text-center rounded-none"
        />
        <Button type="button" onClick={() => updateValue(value + step)} className="rounded-l-none bg-popover h-full px-3">
          +
        </Button>
      </div>
    </div>
  );
}
