import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { type PlayerAssignment } from '@/types/Game';

type TeamPlayers = {
  blue: PlayerAssignment[];
  red: PlayerAssignment[];
}

const intialState: TeamPlayers = {
  blue: [],
  red: []
}

const gameSlice = createSlice({
  name: 'game',
  initialState: intialState,
  reducers: {
    setPlayers(state, action: PayloadAction<TeamPlayers>) {
      state.blue = action.payload.blue;
      state.red = action.payload.red;
    },
  },
})

export const { setPlayers } = gameSlice.actions;
export default gameSlice.reducer;
