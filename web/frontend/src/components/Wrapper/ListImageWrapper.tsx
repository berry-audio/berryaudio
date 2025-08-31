import React from 'react'

const ListImageWrapper = ({children} : {children:React.ReactNode}) => {
  return (
    <div className={`overflow-hidden rounded-[3px] mr-3 w-[44px] grayscale-25 min-w-[44px]`}>
        {children}
    </div>
  )
}

export default ListImageWrapper