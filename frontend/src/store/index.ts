import { configureStore } from "@reduxjs/toolkit";
import gameReducer from "../features/game/gameSlice";
import userReducer from "../features/user/userSlice";

export const store = configureStore({
  reducer: {
    game: gameReducer,
    users: userReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
