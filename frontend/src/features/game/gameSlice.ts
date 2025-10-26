import { createSlice, type PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';
import { type PlayerAssignment } from '@/types/Game';

const API_URL = import.meta.env.VITE_API_URL;

type TeamPlayers = {
  blue: PlayerAssignment[];
  red: PlayerAssignment[];
}

const intialState: TeamPlayers = {
  blue: [],
  red: []
}

interface CreateMatchPayload {
  player1_id: number;
  player2_id: number;
  player3_id: number;
  player4_id: number;
  winner_team: 'blue' | 'red' | 'NONE'; //
}

export const createMatch = createAsyncThunk(
  'game/createMatch',
  async (matchData: CreateMatchPayload) => {
    const response = await fetch('${API_URL}/matches/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(matchData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to submit match');
    }
    return await response.json();
  }
);

const gameSlice = createSlice({
  name: 'game',
  initialState: intialState,
  reducers: {
    setPlayers(state, action: PayloadAction<TeamPlayers>) {
      state.blue = action.payload.blue;
      state.red = action.payload.red;
    },
    
    clearGame(state) {
      state.blue = [];
      state.red = [];
    }
  },

  extraReducers: (builder) => {
    builder
      .addCase(createMatch.pending, (state) => {
      })
      .addCase(createMatch.fulfilled, (state) => {
        state.blue = [];
        state.red = [];
      })
      .addCase(createMatch.rejected, (state, action) => {
        console.error("Match submission failed:", action.error.message);
      });
  }
})

export const { setPlayers } = gameSlice.actions;
export default gameSlice.reducer;
