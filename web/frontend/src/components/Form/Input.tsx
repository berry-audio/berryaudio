import * as React from "react";
import { cn } from "@/lib/utils";
import { XIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

import ButtonIcon from "../Button/ButtonIcon";

interface InputProps extends React.ComponentProps<"input"> {
  onClickClear?: () => void;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, type, onClickClear, ...props }, ref) => {
  return (
    <div className={`w-full relative ${className}`}>
      {!props.disabled && (
        <ButtonIcon onClick={onClickClear} className="top-1 right-2 absolute scale-90 opacity-30">
          <XIcon weight={ICON_WEIGHT} size={ICON_SM}/>
        </ButtonIcon>
      )}

      <input
        ref={ref}
        type={type}
        className={cn(
          "file:text-foreground placeholder:text-muted-foreground selection:bg-primary w-full  selection:text-primary-foreground bg-input h-12 min-w-0 rounded-md px-3 py-1 shadow-xs transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent  file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
          "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
          "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
        )}
        {...props}
      />
    </div>
  );
});
export { Input };
