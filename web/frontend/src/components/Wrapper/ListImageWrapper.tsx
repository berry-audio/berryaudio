import React from 'react'

const ListImageWrapper = ({children} : {children:React.ReactNode}) => {
  return (
    <div className={`overflow-hidden rounded-sm mr-3 grayscale-25 min-w-11 w-11`}>
        {children}
    </div>
  )
}

export default ListImageWrapper