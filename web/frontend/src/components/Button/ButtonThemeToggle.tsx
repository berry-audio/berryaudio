import ButtonIcon from "./ButtonIcon";
import { MoonIcon, SunIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { useTheme } from "@/contexts/ThemeProvider";

const ButtonThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();
  return (
    <ButtonIcon onClick={toggleTheme} className="scale-90">
      {theme === "dark" ? <SunIcon weight={ICON_WEIGHT} size={ICON_SM} /> : <MoonIcon weight={ICON_WEIGHT} size={ICON_SM} />}
    </ButtonIcon>
  );
};

export default ButtonThemeToggle;
