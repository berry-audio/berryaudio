import React, { useState, useRef, useEffect } from "react";
import { AnyAction, Dispatch } from "redux";
import { DotsThreeIcon } from "@phosphor-icons/react";
import { ICON_SM } from "@/constants";

import Spinner from "../Spinner";
import ButtonIcon from "../Button/ButtonIcon";

interface MenuItem {
  name: string;
  icon?: React.ReactNode;
  action:
    | (() => void)
    | (() => Promise<void>)
    | ((dispatch: Dispatch<AnyAction>) => void | Promise<void>);
  disabled?: boolean;
  hide?: boolean;
}

interface ActionMenuProps {
  items: MenuItem[];
}

const ActionMenu: React.FC<ActionMenuProps> = ({ items }) => {
  const [loading, setLoading] = useState<Set<number>>(new Set());
  const [isDropdownOpen, setDropdownOpen] = useState(false);
  const [isDrawerOpen, setDrawerOpen] = useState(false);

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleAction = async (
    index: number,
    action: () => void | Promise<void>
  ) => {
    setLoading((prev) => new Set(prev).add(index));
    try {
      await Promise.resolve(action());
    } finally {
      setLoading((prev) => {
        const next = new Set(prev);
        next.delete(index);
        return next;
      });
      setDropdownOpen(false);
      setDrawerOpen(false);
    }
  };

  const renderButton = (item: MenuItem, idx: number) =>
    !item.hide && (
      <button
        key={idx}
        onClick={() => handleAction(idx, item.action as any)}
        className={`flex w-full items-center gap-2 px-4 py-3 md:py-2 text-left cursor-pointer hover:bg-primary hover:text-primary-foreground bg-popover ${
          item.disabled ? "text-muted! hover:bg-popover disabled:opacity-50" : ""
        }`}
        disabled={item.disabled}
      >
        <div className="mr-2">{loading.has(idx) ? <Spinner /> : item.icon}</div>
        <div>{item.name}</div>
      </button>
    );

  return (
    <div>
      {/* Desktop */}
      <div className="hidden md:block relative" ref={dropdownRef}>
        <ButtonIcon onClick={() => setDropdownOpen((o) => !o)}>
          <DotsThreeIcon size={ICON_SM} />
        </ButtonIcon>

        {isDropdownOpen && (
          <div className="absolute overflow-auto max-h-60 right-0 mt-2 w-48 bg-popover shadow-lg rounded-md z-10">
            {items.map(renderButton)}
          </div>
        )}
      </div>

      {/* Mobile */}
      <div className="md:hidden ">
        <ButtonIcon onClick={() => setDrawerOpen(true)}>
          <DotsThreeIcon size={24} />
        </ButtonIcon>

        {isDrawerOpen && (
          <div
            className="fixed inset-0 z-10 -top-[48px]"
            onClick={() => setDrawerOpen(false)}
          />
        )}

        <div
          className={`fixed overflow-auto max-h-60 bottom-[-1px] left-0 right-0 z-10 rounded-t-sm shadow-lg transform transition-transform duration-200  ${
            isDrawerOpen ? "translate-y-0" : "translate-y-full"
          }`}
        >
          {items.map(renderButton)}
        </div>
      </div>
    </div>
  );
};

export default ActionMenu;
