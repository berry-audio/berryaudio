import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { MusicNoteSimpleIcon } from "@phosphor-icons/react";
import { Ref } from "@/types";
import { REF } from "@/constants/refs";
import { ACTIONS } from "@/constants/actions";
import { INFO_EVENTS } from "@/store/constants";

import useVirtual from "react-cool-virtual";
import NoItems from "@/components/ListItem/NoItems";
import Spinner from "@/components/Spinner";
import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import ListItem from "@/components/ListItem";
import ItemWrapper from "@/components/Wrapper/ItemWrapper";

interface Grid {
  query: REF;
  getDirectory: (uri?: string, limit?: number, offset?: number) => Promise<[]>;
  onClickCallback?: (item: Ref) => void;
  onClickActionCallback?: (action: ACTIONS, item: Ref) => void;
}

const List = ({
  query,
  getDirectory,
  onClickCallback,
  onClickActionCallback,
}: Grid) => {
  const loadMoreCount = 9;
  const action = useSelector((state: any) => state.event);

  const [items, setItems] = useState<any[]>([]);
  const [startOffset, setStartOffset] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const {
    outerRef,
    innerRef,
    items: virtualRows,
    scrollTo,
  } = useVirtual<HTMLDivElement, HTMLDivElement>({
    itemCount: items?.length,
    itemSize: 70,
    loadMoreCount: loadMoreCount,
    loadMore: async ({ startIndex }) => {
      const currentOffset = startIndex;

      if (currentOffset > startOffset) {
        setStartOffset(currentOffset);
        const response = await getDirectory(
          query,
          loadMoreCount,
          currentOffset
        );
        setItems((prev: any) => [...prev, ...response]);
      }
    },
  });

  const fetch = async () => {
    setIsLoading(true);
    const response = await getDirectory(query, loadMoreCount, 0);
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

  return isLoading ? (
    <LayoutHeightWrapper>
      <Spinner />
    </LayoutHeightWrapper>
  ) : !items?.length ? (
    <LayoutHeightWrapper>
      <NoItems
        title="Empty List"
        desc={"Your list is empty. Add items to begin"}
        icon={<MusicNoteSimpleIcon weight={ICON_WEIGHT} size={ICON_SM} />}
      />
    </LayoutHeightWrapper>
  ) : (
    <LayoutHeightWrapper ref={outerRef}>
      <div ref={innerRef}>
        {virtualRows.map(({ index }) => {
          const item = items[index] || [];
          return (
            <ItemWrapper key={index}>
              <ListItem
                item={item}
                onClickCallback={onClickCallback}
                onClickActionCallback={onClickActionCallback}
              />
            </ItemWrapper>
          );
        })}
      </div>
    </LayoutHeightWrapper>
  );
};

export default List;
