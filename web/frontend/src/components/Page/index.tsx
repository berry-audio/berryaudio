import React from "react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { useNavigate } from "react-router-dom";
import { CaretLeftIcon } from "@phosphor-icons/react";

import TruncateText from "../TruncateText";
import ButtonIcon from "../Button/ButtonIcon";

interface Page {
  title?: string;
  backButton?: boolean;
  backButtonOnClick?: () => void;
  centerComponent?: React.ReactNode;
  rightComponent?: React.ReactNode;
  wfull?: boolean;
  children: React.ReactNode;
}
/**
 * Page component
 * Provides a layout wrapper with optional header elements such as a title,
 * back button, centered component, and right-aligned component.
 * @component
 * @param {Object} props - The component props.
 * @param {string} props.title - The title displayed in the page header.
 * @param {boolean} [props.backButton=false] - Whether to show a back button.
 * @param {void} [props.backButtonOnClick] - Back button callback
 * @param {JSX.Element | null} [props.centerComponent] - A custom component displayed in the header center.
 * @param {JSX.Element | null} [props.rightComponent] - A custom component displayed in the header right.
 * @param {boolean} [props.wfull=false] - If true, makes the content area full width.
 * @param {React.ReactNode} props.children - The page content to render inside.
 * @returns {JSX.Element} The rendered page layout.
 */
const Page = ({
  title,
  backButton = false,
  backButtonOnClick,
  centerComponent,
  rightComponent,
  wfull = false,
  children,
}: Page) => {
  const navigate = useNavigate();

  return (
    <div className="h-full overflow-auto">
      <div className="flex justify-between h-[50px]">
        <div
          className={`pl-4 flex items-center ${
            centerComponent ? "w-1/3" : "sm:w-3/3"
          }  justify-items-start`}
        >
          {backButton && (
            <ButtonIcon
              onClick={
                backButtonOnClick ? backButtonOnClick : () => navigate(-1)
              }
            >
              <CaretLeftIcon weight={ICON_WEIGHT} size={ICON_SM} />
            </ButtonIcon>
          )}
          {title && (
            <h2
              className={`text-2xl ${backButton && "ml-2"} font-light dark:text-white`}
            >
              <TruncateText>{title}</TruncateText>
            </h2>
          )}
        </div>
        {centerComponent && (
          <div className="w-1/3  sm:flex justify-center items-center">
            {/* {centerComponent} */}
          </div>
        )}
        {rightComponent && (
          <div className="w-1/3 flex justify-end items-center">
            {rightComponent}
          </div>
        )}
      </div>

      <div className="flex justify-center">
        <div className={`${!wfull && "lg:max-w-[800px]"} w-full`}>
          {children}
        </div>
      </div>
    </div>
  );
};

export default Page;
