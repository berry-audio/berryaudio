import React from "react";
import { useSelector } from "react-redux";

type DateTimeProps = {
  time?: boolean;
  weekday?: boolean;
};

const DateTime: React.FC<DateTimeProps> = ({ time, weekday }) => {
  const { datetime } = useSelector((state: any) => state.system);

  const _datetime = new Date(datetime);

  const timeString = _datetime?.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });

  const weekdayDateString = _datetime?.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <>
      {time && <div>{timeString}</div>}
      {weekday && <div>{weekdayDateString}</div>}
    </>
  );
};

export default DateTime;
