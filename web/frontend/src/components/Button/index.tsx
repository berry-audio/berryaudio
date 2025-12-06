import React from "react";

const Button = ({
  loading,
  children,
  type = "ghost",
  onClick,
  disabled,
}: {
  loading?: boolean;
  children: React.ReactNode;
  type: "ghost" | "primary" | "secondary";
  onClick?: () => void;
  disabled?: boolean;
}) => {
  return (
    <button
      type="submit"
      onClick={onClick}
      disabled={disabled}
      className={`px-6 py-4 transition flex rounded-4xl ${
        type === "ghost" &&
        " hover:bg-neutral-300 dark:hover:bg-neutral-950    disabled:text-neutral-400 dark:disabled:text-neutral-600"
      }  ${type === "primary" && "bg-white hover:bg-neutral-300 text-black"} cursor-pointer ${loading ? 'disabled:bg-neutral-200 dark:disabled:bg-neutral-950 ' : ''}`}
    >
      {loading && (
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin mr-2 rounded-full h-3 w-3 border-2 border-neutral-400 border-t-transparent dark:border-neutral-600 dark:border-t-transparent"></div>
        </div>
      )}
      {children}
    </button>
  );
};

export default Button;
