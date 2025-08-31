import React, { ReactNode } from "react";
import ButtonIcon from "../Button/ButtonIcon";
import Button from "../Button";
interface ModalProps {
  buttonShow?: boolean;
  buttonText?: string;
  buttonLoading?: boolean;
  buttonDisabled?: boolean;
  buttonOnClick?: () => void;
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children?: ReactNode;
  padding?: boolean;
}
const Modal: React.FC<ModalProps> = ({
  buttonShow = true,
  buttonText,
  buttonLoading,
  buttonDisabled,
  buttonOnClick,
  isOpen,
  onClose,
  title,
  children,
  padding = false,
}) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-xs">
      <div className=" dark:bg-neutral-900 bg-neutral-100 rounded-2xl shadow-xl w-full max-w-md mx-4 animate-fadeIn overflow-hidden p-1 z-250 relative">
        {/* Header */}
        <div className="flex justify-between items-center p-5">
          {title && <h2 className="text-2xl font-light">{title}</h2>}
          <ButtonIcon className="-right-4" onClick={onClose}>
            ✕
          </ButtonIcon>
        </div>

        {/* Body */}
        <div className={`overflow-auto max-h-[50vh] ${!padding ? "px-5" : ""}`}>
          {children}
        </div>

        {/* Footer */}
        <div className="flex justify-end p-5">
          {buttonShow && (
            <Button
              type="ghost"
              onClick={buttonOnClick}
              disabled={buttonLoading || buttonDisabled}
              loading={buttonLoading}
            >
              {buttonText ? buttonText : "Ok"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
export default Modal;
