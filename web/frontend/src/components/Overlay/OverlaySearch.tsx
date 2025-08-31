import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { useSearchService } from "@/services/search";
import { MagnifyingGlassIcon } from "@phosphor-icons/react";
import { Input } from "@/components/Form/Input";
import { Ref } from "@/types";
import { ICON_SM, ICON_WEIGHT } from "@/constants";
import { OVERLAY_EVENTS } from "@/store/constants";
import { REF } from "@/constants/refs";

import LayoutHeightWrapper from "@/components/Wrapper/LayoutHeightWrapper";
import ListItem from "@/components/ListItem";
import NoItems from "@/components/ListItem/NoItems";
import Spinner from "@/components/Spinner";
import Overlay from "@/components/Overlay";
import Page from "@/components/Page";
import ItemWrapper from "@/components/Wrapper/ItemWrapper";

type SearchResults = Record<string, Ref[]>;

const OverlaySearch = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { overlay } = useSelector((state: any) => state.overlay);
  const { getSearch } = useSearchService();

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [results, setResults] = useState<SearchResults>({});
  const [query, setQuery] = useState<any>("");

  useEffect(() => {
   
    if (!query.trim()) {
      setResults({});
      setIsLoading(false);
      return;
    }
    const timeoutId = setTimeout(async () => {
      setIsLoading(true);
      const response = await getSearch(query.trim());
      setResults(response);
      setIsLoading(false);
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [query]);

  const title: Record<string, string> = {
    album: "Albums",
    artist: "Artists",
    track: "Tracks",
    genre: "Genre",
    radio: "Radio",
  };

  const handleItemClick = async (item: any) => {
    if (item.type === REF.TRACK) return;
    const [view, id] = item.uri.split(":");
    navigate(`/library/${view}/${id}`);
  };

  return (
    <Overlay
      show={overlay === OVERLAY_EVENTS.OVERLAY_SEARCH}
      zindex={10}
      style={{ zIndex: 100 }}
      hideplayer
    >
      <Page
        title="Search"
        backButtonOnClick={() =>
          dispatch({ type: OVERLAY_EVENTS.OVERLAY_CLOSE })
        }
        backButton
      >
        <div className="px-4 mb-4">
          <Input
            type="text"
            placeholder="Search Albums, Artists, Tracks, Radio..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onClickClear={() => setQuery("")}
          />
        </div>

        <div>
          {isLoading ? (
            <LayoutHeightWrapper>
              <Spinner />
            </LayoutHeightWrapper>
          ) : results && Object.keys(results).length === 0 && query !== "" ? (
            <LayoutHeightWrapper>
              <NoItems
                title="No Results"
                desc="Try with a different keyword"
                icon={
                  <MagnifyingGlassIcon weight={ICON_WEIGHT} size={ICON_SM} />
                }
              />
            </LayoutHeightWrapper>
          ) : (
            results && Object.entries(results).map(([table, items]: [string, Ref[]]) => (
              <div key={table} className="mt-4">
                <h2 className="pl-5 font-bold text-lg">{title[table]}</h2>
                <ul className="list-disc">
                  {results[table] &&
                    items.map((item: Ref, index: number) => (
                      <ItemWrapper key={index}>
                        <ListItem
                          item={item}
                          onClickCallback={handleItemClick}
                        />
                      </ItemWrapper>
                    ))}
                </ul>
              </div>
            ))
          )}
        </div>
      </Page>
    </Overlay>
  );
};

export default OverlaySearch;
