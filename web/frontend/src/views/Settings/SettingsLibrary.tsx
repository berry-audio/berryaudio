import { useEffect, useState } from "react";
import { useConfigService } from "@/services/config";

import Page from "@/components/Page";
import ButtonIcon from "@/components/Button/ButtonIcon";
import TruncateText from "@/components/TruncateText";
import ButtonScanLibrary from "@/components/Button/ButtonScanLibrary";
import ButtonScanArtist from "@/components/Button/ButtonScanArtist";
import ButtonClearLibrary from "@/components/Button/ButtonClearLibrary";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import NoItems from "@/components/ListItem/NoItems";
import {
  FolderIcon,
  StackSimpleIcon,
  TrashSimpleIcon,
} from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";

const SettingsLibrary = () => {
  const { getConfig, setConfig } = useConfigService();

  const [pathList, setPathList] = useState<string[]>();

  useEffect(() => {
    (async () => {
      const config = await getConfig();
      setPathList(config["local"]["library_path"]);
    })();
  }, []);

  const onClickRemovePath = async (path: string) => {
    const current_lib_path = pathList?.length ? pathList : [];
    const updated_lib_path = current_lib_path.filter((item) => item !== path);
    const build_lib_path_config = {
      local: { library_path: updated_lib_path },
    };
    await setConfig(build_lib_path_config);
    setPathList(updated_lib_path);
  };

  return (
    <Page
      backButton
      title="Library Folders"
      rightComponent={
        <div className="flex">
          <div className="mr-4">
            <ButtonScanLibrary disabled={!pathList?.length} />
          </div>
          <div className="mr-4">
            <ButtonScanArtist disabled={!pathList?.length} />
          </div>
          <div className="mr-4">
            <ButtonClearLibrary />
          </div>
        </div>
      }
    >
      {pathList?.length ? (
        <div className="lg:px-0 px-6 py-3">
            {pathList &&
              pathList.map((path: string) => (
                <div
                  key={path}
                  className="pl-4 pr-2 py-2 rounded-sm bg-neutral-200 mt-1 flex items-center justify-between dark:bg-neutral-950 dark:text-white"
                >
                  <div className="flex items-center overflow-hidden">
                    <FolderIcon
                      weight={ICON_WEIGHT}
                      size={ICON_SM}
                      className="mr-2"
                    />
                    <TruncateText>{path}</TruncateText>
                  </div>
                  <ButtonIcon
                    className="text-right ml-5"
                    onClick={() => onClickRemovePath(path)}
                  >
                    <TrashSimpleIcon weight={ICON_WEIGHT} size={ICON_SM} />
                  </ButtonIcon>
                </div>
              ))}
        </div>
      ) : (
        <LayoutHeightWrapper>
          <NoItems
            title="No Folders to Scan"
            desc={"Folders added from Storage will show here"}
            icon={<StackSimpleIcon weight={ICON_WEIGHT} size={ICON_SM} />}
          />
        </LayoutHeightWrapper>
      )}
    </Page>
  );
};

export default SettingsLibrary;
