import { CAMILLA_DSP_URL } from "@/constants";

const SettingsCamillaDsp = () => {
  return (
      <iframe
        src={CAMILLA_DSP_URL}
        title="Camilla DSP"
        style={{
          width: "100%",
          height: "100%",
          border: "none",
        }}
      />
  );
};

export default SettingsCamillaDsp;
