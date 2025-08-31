import React from "react";

const ItemWrapper = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex justify-between items-center w-full cursor-pointer hover:bg-neutral-200 dark:hover:bg-neutral-950 rounded-none lg:rounded-sm transition-all duration-200">
      {children}
    </div>
  );
};

export default ItemWrapper;
