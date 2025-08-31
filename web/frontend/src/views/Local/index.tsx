import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { useNavigate, useParams } from "react-router-dom";
import { useLocalService } from "@/services/local";
import { Ref } from "@/types";
import {
  FolderSimpleIcon,
  GearIcon,
  MusicNotesIcon,
  UserIcon,
  VinylRecordIcon,
} from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { OVERLAY_EVENTS } from "@/store/constants";
import { REF } from "@/constants/refs";
import { ViewMode } from "@/types";

import Page from "@/components/Page";
import ButtonLayoutToggle from "@/components/Button/ButtonLayoutToggle";
import Grid from "../../components/InfiniteScroll/Grid";
import List from "../../components/InfiniteScroll/List";
import ListMenu from "@/components/ListMenu";
import ButtonIcon from "@/components/Button/ButtonIcon";

const Local = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { view, id } = useParams<{ view: REF; id: string }>();
  const { getDirectory } = useLocalService();

  const [layout, setLayout] = useState<ViewMode>("grid");
  const [activeView, setActiveView] = useState<string>();

  const title: Record<string, string> = {
    [REF.ALBUM]: "Albums",
    [REF.ARTIST]: "Artists",
    [REF.GENRE]: "Genre",
    [REF.TRACK]: "Tracks",
  };

  const directories = [
    {
      name: "Artists",
      icon: <UserIcon weight={ICON_WEIGHT} size={ICON_SM} />,
      type: "artist",
    },
    {
      name: "Albums",
      icon: <VinylRecordIcon weight={ICON_WEIGHT} size={ICON_SM} />,
      type: "album",
    },
    {
      name: "Tracks",
      icon: <MusicNotesIcon weight={ICON_WEIGHT} size={ICON_SM} />,
      type: "track",
    },
    {
      name: "Genre",
      icon: <FolderSimpleIcon weight={ICON_WEIGHT} size={ICON_SM} />,
      type: "genre",
    },
  ];

  useEffect(() => {
    (async () => {
      if (id) {
        dispatch({
          type: OVERLAY_EVENTS.OVERLAY_LIBRARY,
          payload: { view, id, activeView },
        });
      }
    })();
  }, [id]);

  /**
   * Handle item click.
   * @param {any} item Item object
   * @returns {*} Plays or navigates from Item
   */
  const handleItemClick = async (item: Ref) => {
    if (item.type === REF.TRACK) return;
    const [view, id] = item.uri.split(":");
    dispatch({
      type: OVERLAY_EVENTS.OVERLAY_LIBRARY,
      payload: { view, id, activeView },
    });
  };

  const onClickHandleDir = (view: string) => {
    setActiveView(view);
    navigate(`/library/${view}`);
  };

  return (
    <>
      {view ? (
        <Page
          wfull={layout === "grid"}
          title={title[view]}
          rightComponent={
            <div className="mr-4">
              <ButtonLayoutToggle
                setLayoutype={setLayout}
                layoutType={layout}
              />
            </div>
          }
          backButtonOnClick={() => navigate("/library")}
          backButton
        >
          {layout === "list" && (
            <List
              query={view}
              getDirectory={getDirectory}
              onClickCallback={handleItemClick}
            />
          )}
          {layout === "grid" && (
            <Grid
              query={view}
              getDirectory={getDirectory}
              onClickCallback={handleItemClick}
            />
          )}
        </Page>
      ) : (
        <Page
          title="Library"
          backButton
          backButtonOnClick={() => navigate("/")}
          rightComponent={
            <div className="mr-4">
              <ButtonIcon onClick={()=>navigate("/settings/library")}>
                <GearIcon weight={ICON_WEIGHT} size={ICON_SM} />
              </ButtonIcon>
            </div>
          }
        >
          {directories.map((dir, index: number) => (
            <ListMenu
              key={index}
              name={dir.name}
              icon={dir.icon}
              onClick={() => onClickHandleDir(dir.type)}
            />
          ))}
        </Page>
      )}
    </>
  );
};

export default Local;
