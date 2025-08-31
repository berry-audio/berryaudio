import React from "react";

/**
 * A simple component that truncates text to a given character limit.
 *
 * @param children - The text to truncate.
 * @param limit - Maximum number of characters to display.
 * @returns JSX element with truncated text.
 */
const TruncateText = ({
  children,
}: {
  children: React.ReactNode;
  title?: string;
  className?: string;
  limit?: number;
}) => {
  return (
    <span className="block overflow-hidden text-ellipsis whitespace-nowrap">
      {children}
    </span>
  );
};

export default TruncateText;
