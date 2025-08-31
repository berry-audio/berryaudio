import { useDispatch, useSelector } from "react-redux";

export const useSocketRequest = () => {
  const dispatch = useDispatch();
  const connected = useSelector((state: any) => state.socket.connected);

  const request = async (method: string, params?: any) => {
    if (!connected) return;
    
    try {
      const response : any = await dispatch({
        type: "socket/request",
        payload: { method, params },
      });

      return response.result; 
    } catch (err) {
      console.error("Socket request failed:", err);
      throw err;
    }
  };

  return { request };
};
