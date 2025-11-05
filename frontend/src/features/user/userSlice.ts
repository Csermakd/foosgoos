import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

const API_URL = import.meta.env.VITE_API_URL;

export interface User {
  id: number;
  name: string;
}

// the state for slice
interface UserState {
  users: User[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null | undefined;
}

const initialState: UserState = {
  users: [],
  status: 'idle',
  error: null,
};

export const fetchAllUsers = createAsyncThunk('users/fetchAll', async () => {
  const response = await fetch(`${API_URL}/users/all`);
  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }
  const data: User[] = await response.json();
  return data;
});

export interface UserCreatePayload {
  name: string;
}

export const createNewUser = createAsyncThunk(
  'users/createNew',
<<<<<<< HEAD
  async (newUser: UserCreatePayload, { dispatch }) => {
=======
  async (newUser: UserCreatePayload) => {
>>>>>>> de29b98 (fixing errors)
    const response = await fetch(`${API_URL}/users/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newUser),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create user');
    }

    dispatch(fetchAllUsers()); 
    return await response.json();
  }
);

// the slice
const userSlice = createSlice({
  name: 'users',
  initialState,
  reducers: {},
  // handling API call results
  extraReducers: (builder) => {
    builder
      .addCase(fetchAllUsers.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchAllUsers.fulfilled, (state, action: PayloadAction<User[]>) => {
        state.status = 'succeeded';
        state.users = action.payload;
      })
      .addCase(fetchAllUsers.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      });
  },
});

export default userSlice.reducer;