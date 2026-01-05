import React from 'react'

const ListImageWrapper = ({children} : {children:React.ReactNode}) => {
  return (
    <div className={`overflow-hidden rounded-[3px] mr-3 grayscale-25 min-w-11`}>
        {children}
    </div>
  )
}

export default ListImageWrapper