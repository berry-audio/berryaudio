import { Middleware } from "@reduxjs/toolkit";
import { WEBSOCKET_URL } from "@/constants";
import { DIALOG_EVENTS, SOCKET_EVENTS } from "./constants";
import { EVENTS } from "@/constants/events";

export const socketMiddleware: Middleware = (store) => {
  let socket: WebSocket | null = null;
  let requestId = 0;
  const pendingRequests = new Map<number, (data: any) => void>();

  let reconnectAttempts = 0;
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

  const connect = () => {
    socket = new WebSocket(WEBSOCKET_URL);

    socket.onopen = () => {
      reconnectAttempts = 0;
      store.dispatch({ type: SOCKET_EVENTS.SOCKET_CONNECTED });
    };

    socket.onclose = () => {
      store.dispatch({ type: SOCKET_EVENTS.SOCKET_DISCONNECTED });

      pendingRequests.forEach((resolve) =>
        resolve(Promise.reject(new Error("Socket disconnected")))
      );
      pendingRequests.clear();

      const delay = Math.min(1000 * 2 ** reconnectAttempts, 3000);
      reconnectAttempts += 1;
      reconnectTimeout = setTimeout(connect, delay);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.error){
          store.dispatch({
            type: DIALOG_EVENTS.DIALOG_ERROR,
            payload: data.error,
          });
          return
        }

        if (data.id && pendingRequests.has(data.id)) {
          pendingRequests.get(data.id)?.(data);
          pendingRequests.delete(data.id);
        } else if (data.event) {
          store.dispatch({
            type: data.event,
            payload: data,
          });
        }
      } catch (err) {
        console.error("Invalid WS message", err);
      }
    };
  };

  connect();

  return (next) => (action: any) => {
    switch (action.type) {
      case "socket/request":
        if (!socket || socket.readyState !== WebSocket.OPEN) {
          return Promise.reject(new Error("Socket not connected"));
        }

        requestId += 1;
        const msg = {
          jsonrpc: "2.0",
          method: action.payload.method,
          params: action.payload.params,
          id: requestId,
        };

        const promise = new Promise((resolve) => {
          pendingRequests.set(requestId, resolve);
        });

        socket.send(JSON.stringify(msg));
        return promise;

      case "socket/disconnect":
        if (reconnectTimeout) clearTimeout(reconnectTimeout);
        if (socket) socket.close();
        socket = null;
        break;
    }
    return next(action);
  };
};
