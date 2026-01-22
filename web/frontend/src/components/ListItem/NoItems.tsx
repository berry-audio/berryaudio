import React from "react";

interface NoItems {
  title: string;
  desc?: React.ReactNode | string;
  icon: React.ReactNode;
}

const NoItems = ({ title, desc, icon }: NoItems) => {
  return (
    <div className="flex w-full h-full flex-col items-center justify-center text-center">
      {icon}
      <h2 className="mt-2 font-medium">{title}</h2>
      {desc && <p className="mb-4 w-80 text-secondary">{desc}</p>}
    </div>
  );
};

export default NoItems;
