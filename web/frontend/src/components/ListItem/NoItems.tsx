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
      <h2 className="mt-2 text-lg">{title}</h2>
      {desc && <p className="mb-4 text-sm w-80 text-neutral-950/50 dark:text-neutral-50/50">{desc}</p>}
    </div>
  );
};

export default NoItems;
