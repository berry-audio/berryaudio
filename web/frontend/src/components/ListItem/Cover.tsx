import { REF } from "@/constants/refs";

import Directory from "./directory";
import TruncateText from "../TruncateText";
import Spinner from "../Spinner";
import React from "react";

interface Cover {
  loading?: boolean;
  type?: REF;
  image?: string;
  title?: string;
  subtitle?: string;
  shadow?: boolean;
  actions?: React.ReactNode;
  onClick?: () => void;
}
/**
 * Cover component
 * Renders a section with an image, title, and description.
 * @param {Object} props - The component props.
 * @param {string} props.type - The type of block.
 * @param {string} props.loading - Shows or hides loading.
 * @param {string} props.image - The URL or path of the image to display.
 * @param {string} props.title - The main heading text.
 * @param {string} props.subtitle - A short descriptive text below the title.
 * @param {boolean} props.shadow - Shows or hides shadow.
 * @param {React.ReactNode} props.actions - attach component as menu.
 * @returns {JSX.Element} The rendered cover section.
 */
const Cover = ({ type = REF.TRACK, loading = false, image, title, subtitle, shadow = false, actions, onClick }: Cover) => {
  return (
    <div className="w-full">
      <button onClick={onClick} className="w-full cursor-pointer  shadow-1xl">
        <div
          className={`overflow-hidden rounded-md transition-all relative  ${
            shadow ?? "shadow-[1px_14px_21px_-6px_rgba(0,0,0,0.1)]"
          }`}
        >
          {loading && (
            <div className="absolute w-full h-full flex items-center justify-center z-10 dark:bg-black/80 bg-white/80">
              <Spinner />
            </div>
          )}

          {image ? <img src={image} alt={title} className="object-cover w-full scale-101 aspect-square grayscale-25 " /> : <Directory type={type} />}
        </div>
      </button>
      <div className="flex justify-between">
        <div className="overflow-hidden text-left">
          {title && (
            <h2 className={`text-lg font-medium tracking-tight `}>
              <TruncateText>{title}</TruncateText>
            </h2>
          )}

          {subtitle && (
            <div className="text-secondary font-medium">
              <TruncateText>{subtitle}</TruncateText>
            </div>
          )}
        </div>
        {actions && <div className="-mr-2">{actions}</div>}
      </div>
    </div>
  );
};

export default React.memo(Cover);
