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
      className={`p-4 transition flex rounded-4xl ${type=== 'ghost' && ' hover:bg-neutral-200 dark:hover:bg-neutral-950  text-yellow-700 dark:text-yellow-700 disabled:text-white dark:disabled:text-white'}  ${type=== 'primary' && 'bg-white hover:bg-neutral-200 text-black'} cursor-pointer disabled:bg-neutral-500 disabled:opacity-30 `}
    >
      {loading && (
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin mr-2 rounded-full h-3 w-3 border-2 border-white border-t-transparent dark:border-neutral-50 dark:border-t-transparent"></div>
        </div>
      )}
      {children}
    </button>
  );
};

export default Button;
