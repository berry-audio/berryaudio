import React, { forwardRef } from "react";

interface LayoutHeightWrapper  {
  children: React.ReactNode;
  className?: string;
};

const LayoutHeightWrapper = forwardRef<HTMLDivElement, LayoutHeightWrapper>(
  ({ children, className }, ref) => {
    return (
      <div
        ref={ref}
        className={`h-[calc(100dvh-170px)] lg:h-[calc(100dvh-180px)] overflow-auto ${className ?? ""}`}
      >
        {children}
      </div>
    );
  }
);

export default LayoutHeightWrapper;
