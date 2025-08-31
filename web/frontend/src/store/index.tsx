import { configureStore } from "@reduxjs/toolkit";
import { socketMiddleware } from "./socketMiddleware";
import { rootReducer } from "./reducers";

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefault) => getDefault().concat(socketMiddleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
