import { MusicNotesIcon } from "@phosphor-icons/react";
import { formatNo } from "@/util";
import { REF } from "@/constants/refs";

import React from "react";
import Directory from "./directory";
import TruncateText from "../TruncateText";
import Spinner from "../Spinner";
import ListImageWrapper from "../Wrapper/ListImageWrapper";

interface CoverList {
  type?: REF;
  no?: number;
  loading?: boolean;
  image?: string;
  title: string;
  subtitle?: string | React.ReactNode;
  duration?: string;
  selected?: boolean;
}
/**
 * CoverList component
 * Renders a list-style cover block that can represent different entity types
 * (e.g.,cover, track, album, artist) along with an image, title, and description.
 * @component
 * @param {Object} props - The component props.
 * @param {string} [props.type=REF.TRACK] - The type of cover (defaults to track).
 * @param {string} props.loading - Shows or hides loading.
 * @param {string} props.image - The URL or path of the image to display.
 * @param {string} props.title - The main heading text.
 * @param {string} props.subtitle - A short descriptive text below the title.
 * @param {string} props.selected - Highlighted
 * @returns {JSX.Element} The rendered cover list element.
 */
const CoverList = ({
  type = REF.TRACK,
  no,
  loading = false,
  image,
  title,
  subtitle,
  duration,
  selected = false,
}: CoverList) => {
  return (
    <div className="flex items-center w-full">
      {no && (
        <div className="-ml-1 mr-4 text-sm text-neutral-500 w-[10px] text-center">
          {formatNo(no)}
        </div>
      )}
      <ListImageWrapper>
        {loading && (
          <div className="absolute w-full h-full flex items-center justify-center z-10 dark:bg-black/80 bg-white/80">
            <Spinner />
          </div>
        )}
        {image ? (
          <img
            src={image}
            alt={title}
            className="object-cover aspect-square w-full grayscale-25"
          />
        ) : (
          <Directory type={type} />
        )}
      </ListImageWrapper>
      <div className="text-left flex-grow w-0 pr-5">
        <h2 className={`text-lg font-medium tracking-tight dark:text-white flex`}>
          <TruncateText>{title}</TruncateText>
          {selected && (
            <MusicNotesIcon
              className="text-yellow-700 inline-block ml-1 mt-[6px]"
              weight={'fill'}
              size={15}
              
            />
          )}
        </h2>
        {
          subtitle && (
             <div className={`${window.innerHeight < 400 ? "mt-0" : "-mt-1"} text-neutral-500 font-medium`}>
          <TruncateText>{subtitle as string}</TruncateText>
        </div>
          )
        }
       
      </div>
      {duration && <div className="mr-2 text-neutral-500 text-sm">{duration}</div>}
    </div>
  );
};

export default React.memo(CoverList);
