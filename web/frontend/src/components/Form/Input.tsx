import * as React from "react";
import { cn } from "@/lib/utils";
import { XIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "../Button/ButtonIcon";

interface InputProps extends React.ComponentProps<"input"> {
  onClickClear?: () => void;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, onClickClear, ...props }, ref) => {
    return (
      <div className="w-full relative">
        <ButtonIcon onClick={onClickClear} className="top-1.5 right-2 absolute scale-90 opacity-20">
          <XIcon
            weight={ICON_WEIGHT}
            size={ICON_SM}
            className="dark:text-white text-black"
          />
        </ButtonIcon>
        <input
          ref={ref}
          type={type}
          className={cn(
            "file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground dark:bg-neutral-950 bg-white flex w-full min-w-0 border text-base shadow-xs transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-md",
            "transition-all hover:bg-white p-4 rounded-sm",
            "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive p-3 w-full",
            className
          )}
          {...props}
        />
      </div>
    );
  }
);
export { Input };
