import React, { useEffect, useState } from "react";
import { useSystemService } from "@/services/system";
import { formatSize } from "@/util";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { CpuIcon, HardDriveIcon, MemoryIcon } from "@phosphor-icons/react";

import Page from "@/components/Page";
import Spinner from "@/components/Spinner";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";

export interface SystemInfo {
  os: string;
  hostname: string;
  model: string;
  software: string;
  version: string;
  cpu: {
    volts: number;
    usage_percent: number;
    cores: number;
    temperature: number;
  };
  memory: {
    mem_used: number;
    mem_total: number;
    mem_percent: number;
  };
  disk: {
    disk_used: number;
    disk_total: number;
    disk_percent: number;
  };
   network: {
    lo: string;
    wlan0: string;
  };
}

const defaultSystemInfo: SystemInfo = {
  os: "unknown",
  hostname: "unknown",
  model: "unknown",
  software: "unknown",
  version: "unknown",
  cpu: {
    volts: 0,
    usage_percent: 0,
    cores: 0,
    temperature: 0,
  },
  memory: {
    mem_used: 0,
    mem_total: 0,
    mem_percent: 0,
  },
  disk: {
    disk_used: 0,
    disk_total: 0,
    disk_percent: 0,
  },
  network: {
    lo: 'None',
    wlan0: 'None',
  },
};

const SettingsAbout = () => {
  const { getSystemInfo } = useSystemService();
  const [systemInfo, setSystemInfo] = useState<SystemInfo>(defaultSystemInfo);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    setIsLoading(true);
    const fetchSystemInfo = async () => {
      try {
        const response = await getSystemInfo();
        setSystemInfo(response);
        setIsLoading(false);
      } catch (error) {
        console.error("Failed to fetch system info", error);
      }
    };
    fetchSystemInfo();

    const interval = setInterval(() => {
      fetchSystemInfo();
    }, 10000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const ListHardwareItem = ({
    title,
    desc,
  }: {
    title: string;
    desc: string;
  }) => {
    return (
      <div className="flex mt-2 text-secondary">
        <div className="w-25 flex">{title}:</div>
        <div className="flex-1 flex flex-col">{desc}</div>
      </div>
    );
  };

  const ListUsageItem = ({
    title,
    desc,
    percent,
  }: {
    title: React.ReactNode;
    desc: string;
    percent: number;
  }) => {
    return (
      <div>
        <div className="font-medium flex items-center">{title}</div>
        <div className="w-full">
          <div className="mb-1 text-secondary">{desc}</div>
          <div className="w-full bg-popover rounded-full h-1 mt-3 mb-1">
            <div
              className="bg-primary h-1 rounded-full"
              style={{ width: `${percent}%` }}
            ></div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Page backButton title="About">
      {isLoading ? (
        <LayoutHeightWrapper>
          <Spinner />
        </LayoutHeightWrapper>
      ) : (
        <div className="px-5 py-3">
          <ListUsageItem
            title={
              <>
                <HardDriveIcon
                  weight={ICON_WEIGHT}
                  size={ICON_SM}
                  className="mr-2"
                />
                Disk
              </>
            }
            desc={`${formatSize(
              systemInfo?.disk?.disk_used
            )} used of ${formatSize(systemInfo?.disk?.disk_total)}`}
            percent={systemInfo?.disk?.disk_percent}
          />
          <div className="w-full grid xs:grid-cols-2 gap-4 grid-cols-2 mt-6">
            <ListUsageItem
              title={
                <>
                  <CpuIcon
                    weight={ICON_WEIGHT}
                    size={ICON_SM}
                    className="mr-2"
                  />
                  CPU
                </>
              }
              desc={`${systemInfo?.cpu?.usage_percent}% ${systemInfo?.cpu?.temperature}°C (Cores ${systemInfo?.cpu?.cores}) `}
              percent={systemInfo?.cpu?.usage_percent}
            />

            <ListUsageItem
              title={
                <>
                  <MemoryIcon
                    weight={ICON_WEIGHT}
                    size={ICON_SM}
                    className="mr-2"
                  />
                  Memory
                </>
              }
              desc={`${systemInfo?.memory?.mem_used.toFixed(
                2
              )}GB used of ${systemInfo?.memory?.mem_total.toFixed(2)}GB`}
              percent={systemInfo?.memory?.mem_percent}
            />
          </div>

          <div className="mt-6">
            <div className="text-lg font-medium mb-2">Hardware</div>
            <ListHardwareItem title="Model" desc={systemInfo?.model} />
            <ListHardwareItem title="OS" desc={systemInfo?.os} />
            <ListHardwareItem title="Version" desc={systemInfo?.version} />
            <ListHardwareItem title="Hostname" desc={systemInfo?.hostname} />
            <ListHardwareItem title="Software" desc={systemInfo?.software} />
          </div>
        </div>
      )}
    </Page>
  );
};

export default SettingsAbout;
