import React from "react";

const ButtonIcon = ({
  children,
  className,
  disabled = false,
  onClick,
}: {
  children: React.ReactNode;
  className?: string;
  disabled?:boolean;
  onClick?: () => void;
}) => {
  return (
    <button
      className={`cursor-pointer flex hover:bg-button-hover w-10 h-10 items-center justify-center rounded-full disabled:opacity-30 transition-all duration-200 ${className ? className : ""} `}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

export default ButtonIcon;
