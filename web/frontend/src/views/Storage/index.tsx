import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { useConfigService } from "@/services/config";
import { useStorageService } from "@/services/storage";
import { EjectSimpleIcon, HardDriveIcon } from "@phosphor-icons/react";
import { StorageDevice, StorageInfo, Ref } from "@/types";
import { formatBytes, splitUri } from "@/util";
import { ACTIONS } from "@/constants/actions";
import { ICON_SM, ICON_WEIGHT, ICON_XS } from "@/constants";
import { REF } from "@/constants/refs";

import Page from "@/components/Page";
import Spinner from "@/components/Spinner";
import ActionMenu from "@/components/Actions";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import ListItem from "@/components/ListItem";
import ItemWrapper from "@/components/Wrapper/ItemWrapper";
import ItemPadding from "@/components/Wrapper/ItemPadding";

const Storage = () => {
  const navigate = useNavigate();

  const { getStorage, getDir, setMount, setUnMount } = useStorageService();
  const { setConfig, getConfig } = useConfigService();
  const { storage } = useSelector((state: any) => state.storage);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [dirlist, setDirList] = useState<any[]>([]);
  const [dirCur, setDirCur] = useState<string>();
  const [storages, setStorages] = useState<StorageInfo>({
    mounted: [],
    unmounted: [],
  });

  useEffect(() => {
    setStorages((prev) => {
      const newState: StorageInfo = { ...prev };
      Object.keys(prev).forEach((key) => {
        const _storage = prev[key as keyof StorageInfo] as StorageDevice[];
        newState[key as keyof StorageInfo] = _storage.filter(
          (i) => i.dev !== storage.dev
        );
      });
      if (storage.status !== "removed") {
        const status = storage.status as keyof StorageInfo;
        if (status) {
          newState[status] = [...newState[status], { ...storage }];
        }
      }
      return newState;
    });
  }, [storage]);

  const onClickActionMenu = async (action: ACTIONS, item: Ref) => {
    const current_settings = await getConfig();

    if (action === "add_library") {
      const uri = splitUri(item.uri);
      const current_lib_path = current_settings["local"]["library_path"].length
        ? current_settings["local"]["library_path"]
        : [];
      current_lib_path.push(uri.id);
      const updated_lib_path_config = {
        local: { library_path: current_lib_path },
      };
      await setConfig(updated_lib_path_config);
    }
  };

  const onClickHandler = async (item: Ref) => {
    if (item.type === REF.FOLDER) {
      const uri = splitUri(item.uri);
      fetchDir(uri.id);
    }
  };

  const onClickActionHandler = async (action: string, dev: string) => {
    if (action === "mount") {
      await setMount(dev);
    } else if (action === "unmount") {
      await setUnMount(dev);
    }
  };

  const onClickDirBackHandler = () => {
    setDirList([]);
    navigate("/storage");
  };

  const onClickBackHandler = () => {
    navigate("/");
  };

  const fetchDir = async (path: string) => {
    setIsLoading(true);
    const res = await getDir(path);
    const cur_dir = path.split("/");
    setDirList(res);
    setDirCur(cur_dir[cur_dir?.length-1])
    navigate(`/storage/browse`);
    setIsLoading(false);
  };

  const fetchStorages = async () => {
    setIsLoading(true);
    const res = await getStorage();
    setStorages(res);
    setIsLoading(false);
  };

  useEffect(() => {
    fetchStorages();
  }, []);

  const ListItemStorage = ({
    item,
    mounted,
  }: {
    item: StorageDevice;
    mounted: boolean;
  }) => {
    const actionItems = [
      {
        name: "Mount",
        icon: <HardDriveIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: () => onClickActionHandler("mount", item.dev),
      },
      {
        name: "Eject",
        icon: <EjectSimpleIcon size={ICON_XS} weight={ICON_WEIGHT} />,
        action: () => onClickActionHandler("unmount", item.dev),
      },
    ];

    return (
      <div className="w-full">
        <div className="flex justify-between">
          <button
            onClick={() => mounted && fetchDir(item.mount)}
            className="cursor-pointer w-full"
          >
            <div className="text-lg font-medium">
              <div className="w-full flex">
                <div className="flex">
                  <HardDriveIcon
                    weight={ICON_WEIGHT}
                    size={ICON_SM}
                    className="mr-2"
                  />
                  {item.label}
                </div>
              </div>
              <div className="mb-1  text-neutral-500 text-left">{`${
                mounted
                  ? `${formatBytes(item.free)} available of ${formatBytes(
                      item.total
                    )}`
                  : "Unmounted"
              }`}</div>
            </div>
          </button>
          <div className="-mr-2">
            <ActionMenu items={actionItems} />
          </div>
        </div>

        <div className="w-full dark:bg-neutral-950 bg-gray-200 rounded-full h-[3px] mt-3 mb-1">
          <div
            className={`${mounted ? "bg-yellow-700" : ""} h-[3px] rounded-full`}
            style={{ width: `${item.percent}%` }}
          ></div>
        </div>
      </div>
    );
  };

  return dirlist?.length > 0 ? (
    <Page
      backButton
      backButtonOnClick={onClickDirBackHandler}
      title={dirCur || "Storage"}
    >
      {isLoading ? (
        <LayoutHeightWrapper>
          <Spinner />
        </LayoutHeightWrapper>
      ) : (
        dirlist.map((dir, index) => (
          <ItemWrapper key={index}>
            <ListItem
              item={
                {
                  uri: `storage:${dir.path}`,
                  name: dir.name,
                  type: dir.type,
                } as Ref
              }
              onClickCallback={onClickHandler}
              onClickActionCallback={onClickActionMenu}
            />
          </ItemWrapper>
        ))
      )}
    </Page>
  ) : (
    <Page backButton backButtonOnClick={onClickBackHandler} title="Storage">
      {isLoading ? (
        <LayoutHeightWrapper>
          <Spinner />
        </LayoutHeightWrapper>
      ) : (
        Object.keys(storages).map((key) => {
          const storage: StorageDevice[] = storages[key as keyof StorageInfo];

          return storage.map((item: StorageDevice) => (
            <ItemWrapper key={item.dev}>
              <ItemPadding>
                <ListItemStorage mounted={key === "mounted"} item={item} />
              </ItemPadding>
            </ItemWrapper>
          ));
        })
      )}
    </Page>
  );
};
export default Storage;
