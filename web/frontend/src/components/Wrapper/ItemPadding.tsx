import React from "react";

const ItemPadding = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="py-3 px-4 flex justify-between w-full relative items-center">
      {children}
    </div>
  );
};

export default ItemPadding;
