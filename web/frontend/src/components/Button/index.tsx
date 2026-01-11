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
      className={`px-6 py-4 transition flex rounded-4xl ${type === "ghost" && " hover:bg-button-hover disabled:opacity-50 "}  ${
        type === "primary" && " hover:bg-neutral-300 "
      } cursor-pointer ${loading ? "disabled:opacity-50" : ""}`}
    >
      {loading && (
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin mr-2 rounded-full h-3 w-3 border-2 loader-foreground"></div>
        </div>
      )}
      {children}
    </button>
  );
};

export default Button;
