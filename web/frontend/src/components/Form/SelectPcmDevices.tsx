import { useEffect, useState } from "react";
import { Button } from "../ui/Button";
import { useMixerService } from "@/services/mixer";
import { PcmDevice } from "@/types";

import { cn } from "@/lib/utils";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CheckIcon, ChevronsUpDownIcon } from "lucide-react";

function SelectPcmDevices({ label, items, onChange }: Props) {
  const { getPlaybackDevices } = useMixerService();
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");

  console.log("Selected device:", value);

  const [pcmDevices, setPcmDevices] = useState<PcmDevice[]>([]);

  const fetchPlaybackDevices = async () => {
    const response = await getPlaybackDevices();
    console.log(response);
    setPcmDevices(response);
  };

  useEffect(() => {
    fetchPlaybackDevices();
  }, []);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" role="combobox" aria-expanded={open} className="w-[200px] justify-between">
          {value ? pcmDevices.find((device) => device.device === value)?.card_name : "Select device"}
          <ChevronsUpDownIcon className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0">
        <Command>
          <CommandInput placeholder="Search devices..." />
          <CommandList>
            <CommandEmpty>No devices found.</CommandEmpty>
            <CommandGroup>
              {pcmDevices?.map((device) => (
                <CommandItem
                  key={device.device}
                  value={device.device}
                  onSelect={(currentValue) => {
                    setValue(currentValue === value ? "" : currentValue);
                    setOpen(false);
                  }}
                >
                  <CheckIcon className={cn("mr-2 h-4 w-4", value === device.device ? "opacity-100" : "opacity-0")} />
                  {device.card_name}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

export default SelectPcmDevices;
