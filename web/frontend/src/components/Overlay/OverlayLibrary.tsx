import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useLocalService } from "@/services/local";
import { getArtists, getImage } from "@/util";
import { useNavigate } from "react-router-dom";
import { OVERLAY_EVENTS } from "@/store/constants";
import { CaretDownIcon } from "@phosphor-icons/react";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { Ref } from "@/types";

import Page from "@/components/Page";
import Spinner from "@/components/Spinner";
import TruncateText from "@/components/TruncateText";
import Overlay from "@/components/Overlay";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import ListItem from "@/components/ListItem";
import Cover from "@/components/ListItem/Cover";
import ItemWrapper from "@/components/Wrapper/ItemWrapper";
import ButtonIcon from "@/components/Button/ButtonIcon";
import FavouriteButton from "@/components/Player/FavouriteButton";
import ButtonAddToQueue from "@/components/Button/ButtonAddToQueue";
import ButtonPlayAll from "@/components/Button/ButtonPlayAll";
import ButtonAddToPlaylist from "@/components/Button/ButtonAddToPlaylist";
import ButtonInfo from "@/components/Button/ButtonInfo";
import { REF } from "@/constants/refs";

const OverlayLibrary = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { getDirectory } = useLocalService();
  const { overlay, payload } = useSelector((state: any) => state.overlay);

  const [item, setItem] = useState<Ref>();
  const [itemsDetailList, setItemsDetailList] = useState<any[]>([]);
  const [isItemDetailLoading, setIsItemDetailLoading] = useState<boolean>(true);

  const uri = `${payload?.view}:${payload?.id}`;

  const fetchDetail = async (query: string) => {
    const response = await getDirectory(query);
    setItem(response[0]);
  };

  const fetchDetailList = async (query: string) => {
    const responseDetaiList = await getDirectory(query);
    setItemsDetailList(responseDetaiList);
  };

  const handleDetailClose = () => {
    if (payload?.activeView) {
      window.history.pushState({}, "", `/library/${payload.view}`);
    } else {
      navigate(-1);
    }
    setIsItemDetailLoading(true);
    setItem(undefined);
    setItemsDetailList([]);
    dispatch({ type: OVERLAY_EVENTS.OVERLAY_CLOSE });
  };

  useEffect(() => {
    if (!payload?.view && !payload?.id) return;
    (async () => {
      await fetchDetailList(`${uri}:list`);
      await fetchDetail(`${uri}`);
      setIsItemDetailLoading(false);
      navigate(`/library/${payload.view}/${payload.id}`, { replace: true });
    })();
  }, [payload?.view, payload?.id]);

  return (
    <Overlay
      show={overlay === OVERLAY_EVENTS.OVERLAY_LIBRARY}
      zindex={10}
      hideplayer
    >
      <Page backButtonOnClick={handleDetailClose}>
        {isItemDetailLoading ? (
          <LayoutHeightWrapper>
            <Spinner />
          </LayoutHeightWrapper>
        ) : (
          <>
            <div className="justify-center flex -mt-10 relative">
              <ButtonIcon
                className="hover:bg-black opacity-60 z-51 absolute -top-2 right-4"
                onClick={() => dispatch({ type: OVERLAY_EVENTS.OVERLAY_CLOSE })}
              >
                <CaretDownIcon weight={ICON_WEIGHT} size={ICON_SM} />
              </ButtonIcon>

              <div className="w-full px-4">
                {item && (
                  <div className="flex">
                    <div className="justify-center flex w-2/5">
                      <div className="mr-4 w-full">
                        <Cover
                          type={item?.type}
                          image={getImage(item?.images?.[0]?.uri)}
                        />
                      </div>
                    </div>

                    <div className="w-3/5">
                      <h2 className="text-2xl font-semibold max-w-52">
                        <TruncateText>{item?.name}</TruncateText>
                      </h2>

                      {item?.performers.length ? (
                        <div className="text-sm dark:text-neutral-100 text-neutral-900 mt-1">
                          <TruncateText>
                            Performers : {getArtists(item.artists)}
                          </TruncateText>
                        </div>
                      ) : null}

                      {item?.date && (
                        <div className="text-sm dark:text-neutral-100 text-neutral-900 mt-1">
                          <TruncateText>Released on {item?.date}</TruncateText>
                        </div>
                      )}

                      {item?.genre && (
                        <div className="text-sm dark:text-neutral-100 text-neutral-900 mt-1">
                          <TruncateText>Genre : {item?.genre}</TruncateText>
                        </div>
                      )}

                      {item?.country && (
                        <div className="text-sm dark:text-neutral-100  text-neutral-900 mt-1">
                          <TruncateText>Country : {item?.country}</TruncateText>
                        </div>
                      )}
                      {/* {itemsDetail?.comment && (
                        <div className="text-sm text-secondary mt-3 mb-5">
                          <TruncateText>{itemsDetail?.comment}</TruncateText>
                        </div>
                      )} */}

                      <div className="flex items-center mt-2">
                        <div className="mr-1 -ml-3">
                          <ButtonPlayAll item={item} />
                        </div>

                        <div className="mr-1">
                          <ButtonAddToQueue item={item} />
                        </div>

                        <div className="mr-1">
                          <FavouriteButton />
                        </div>

                        <div className="mr-1">
                          <ButtonAddToPlaylist item={item} />
                        </div>

                        {payload?.view === REF.ARTIST && (
                          <div className="mr-1">
                            <ButtonInfo item={item}/>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="w-full">
              {itemsDetailList.length &&
                itemsDetailList.map((item: any, index: number) => (
                  <ItemWrapper>
                    <ListItem item={item} index={index} key={index} />
                  </ItemWrapper>
                ))}
            </div>
          </>
        )}
      </Page>
    </Overlay>
  );
};

export default OverlayLibrary;
