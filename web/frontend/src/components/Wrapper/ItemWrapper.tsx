import React from "react";

const ItemWrapper = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex justify-between items-center w-full cursor-pointer hover:bg-button-hover rounded-none lg:rounded-md transition-all duration-200">
      {children}
    </div>
  );
};

export default ItemWrapper;
