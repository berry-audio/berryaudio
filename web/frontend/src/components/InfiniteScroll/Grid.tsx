import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { MusicNotesSimpleIcon } from "@phosphor-icons/react";
import { Ref } from "@/types";
import { REF } from "@/constants/refs";
import { ACTIONS } from "@/constants/actions";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { DIALOG_EVENTS, INFO_EVENTS } from "@/store/constants";

import Spinner from "@/components/Spinner";
import NoItems from "@/components/ListItem/NoItems";
import useVirtual from "react-cool-virtual";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import ListItem from "@/components/ListItem";

interface Grid {
  query: REF;
  getDirectory: (uri?: string, limit?: number, offset?: number) => Promise<[]>;
  onClickCallback?: (item: any) => void;
  onClickActionCallback?: (action: ACTIONS, item: Ref) => void;
}

const calculateCols = () => {
  if (window.innerWidth < 576) return 2;
  else if (window.innerWidth < 940) return 4;
  else if (window.innerWidth < 1024) return 5;
  else if (window.innerWidth < 1440) return 6;
  else if (window.innerWidth < 1600) return 7;
  else return 8;
};

const Grid = ({
  query,
  getDirectory,
  onClickCallback,
  onClickActionCallback,
}: Grid) => {
  const dispatch = useDispatch();

  const loadMoreCount = 3;
  const action = useSelector((state: any) => state.event);

  const [items, setItems] = useState<any[]>([]);
  const [startOffset, setStartOffset] = useState<number>(0);
  const [columns, setColumns] = useState(calculateCols());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const {
    outerRef,
    innerRef,
    items: virtualRows,
    scrollTo,
  } = useVirtual<HTMLDivElement, HTMLDivElement>({
    itemCount: Math.ceil(items?.length / columns),
    itemSize: 280,
    loadMoreCount: loadMoreCount,
    loadMore: async ({ startIndex }) => {
      const currentOffset = startIndex * columns;

      if (currentOffset > startOffset) {
        setStartOffset(currentOffset);
        const response = await getDirectory(
          query,
          loadMoreCount * columns,
          currentOffset
        );
        setItems((prev: any) => [...prev, ...response]);
      }
    },
  });

  const fetch = async () => {
    setIsLoading(true);

    const response = await getDirectory(query, loadMoreCount * columns, 0) || [];
    if(!response.length && [REF.ARTIST, REF.ALBUM, REF.GENRE, REF.TRACK].includes(query)){
      dispatch({ type: DIALOG_EVENTS.DIALOG_ADD_LIBRARY })
    }

    setItems(response);
    setStartOffset(0);
    scrollTo(0);
    setIsLoading(false);
  };

  useEffect(() => {
    if (action.event === INFO_EVENTS.PLAYLISTS_UPDATED) {
      fetch();
    }
  }, [action]);

  useEffect(() => {
    fetch();
  }, [query]);


  useEffect(() => {
    const handler = () => {
      setColumns(calculateCols());
    };
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  return isLoading ? (
    <LayoutHeightWrapper>
      <Spinner />
    </LayoutHeightWrapper>
  ) : !items?.length ? (
    <LayoutHeightWrapper>
      <NoItems
        title="Empty Library"
        desc={"Your library is empty. Add music to begin"}
        icon={<MusicNotesSimpleIcon weight={ICON_WEIGHT} size={ICON_SM} />}
      />
    </LayoutHeightWrapper>
  ) : (
    <LayoutHeightWrapper ref={outerRef}>
      <div ref={innerRef} className="px-3">
        {virtualRows.map(({ index }) => {
          const start = index * columns;
          const rowItems = items.slice(start, start + columns) || [];
          return (
            <div key={index} className="flex items-start">
              {rowItems.map((item: any, index: number) => (
                <ListItem
                  item={item}
                  key={index}
                  style={{ width: `${100 / columns}%` }}
                  className="p-4 pb-6"
                  onClickCallback={onClickCallback}
                  onClickActionCallback={onClickActionCallback}
                  cover
                />
              ))}
            </div>
          );
        })}
      </div>
    </LayoutHeightWrapper>
  );
};

export default Grid;
