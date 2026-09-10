import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./slices/authSlice";
import reportsReducer from "./slices/reportsSlice";
import chatSessionsReducer from "./slices/chatSessionsSlice";

export const makeStore = () =>
  configureStore({
    reducer: {
      auth: authReducer,
      reports: reportsReducer,
      chatSessions: chatSessionsReducer,
    },
    devTools: process.env.NODE_ENV !== "production",
  });

export type AppStore = ReturnType<typeof makeStore>;
export type RootState = ReturnType<AppStore["getState"]>;
export type AppDispatch = AppStore["dispatch"];
