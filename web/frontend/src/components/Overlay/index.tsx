import React from "react";
import clsx from "clsx";
/**
 * Overlay component
 *
 * Displays a full-width, fixed-position panel below a 48 px header.
 * It can fade/slide in or out and allows scrollable content inside.
 *
 * @param {object} props
 * @param {React.ReactNode} props.children - Content to render inside the overlay.
 * @param {boolean} props.show - Whether the overlay is visible.
 * @param {boolean} props.overlay - Whether the overlay is full or partial.
 * @param {number} props.zindex - z-index for controlling stacking order.
 * @param {string} props.className - classnames
 * @param {object} props.style - classnames
 * @param {() => void} props.onClick - onClick
 * @returns {JSX.Element} The rendered overlay.
 */
const Overlay = ({
  children,
  show,
  full = false,
  overlay = false,
  hideplayer = false,
  zindex = 10,
  className,
  style = {},
  onClick,
}: {
  children: React.ReactNode;
  show: boolean;
  full?: boolean;
  overlay?: boolean;
  hideplayer?: boolean;
  zindex: number;
  className?: string;
  style?: object;
  onClick?: () => void;
}) => {
  return (
    <div
      className={clsx(
        overlay
          ? "bg-background w-full h-[100vh] absolute flex justify-center items-center text-center top-0 left-0 right-0"
          : `bg-background w-full ${
              full
                ? "top-[0px] bottom-0"
                : `top-[48px] ${
                    hideplayer
                      ? "bottom-[0px]"
                      : "lg:bottom-[82px] bottom-[70px]"
                  }`
            } fixed transition-transform duration-300 ease-in-out left-0`,
        show
          ? "translate-y-0"
          : "pointer-events-none translate-y-full",
        overlay && !show && "hidden",
        ` ${className}`
      )}
      onClick={onClick}
      style={{...style, zIndex:zindex}}
    >
      {children}
    </div>
  );
};

export default Overlay;
