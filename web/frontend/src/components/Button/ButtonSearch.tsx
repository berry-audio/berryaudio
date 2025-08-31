import { useDispatch } from 'react-redux';
import { MagnifyingGlassIcon } from '@phosphor-icons/react';
import { OVERLAY_EVENTS } from '@/store/constants';
import { ICON_SM, ICON_WEIGHT } from '@/constants';

import ButtonIcon from "@/components/Button/ButtonIcon";

const ButtonSearch = () => {
  const dispatch = useDispatch();
    
  return (
     <ButtonIcon onClick={()=>dispatch({ type: OVERLAY_EVENTS.OVERLAY_SEARCH })} className="scale-90">
        <MagnifyingGlassIcon weight={ICON_WEIGHT} size={ICON_SM} />
      </ButtonIcon>
  )
}

export default ButtonSearch