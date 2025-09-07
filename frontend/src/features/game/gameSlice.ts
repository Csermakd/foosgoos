import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

type TeamPlayers = {
    blue: string[];
    red: string[];
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
