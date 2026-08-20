import {
  createSlice,
  type PayloadAction,
  createAsyncThunk,
} from "@reduxjs/toolkit";
import {
  type PlayerAssignment,
  type GoalEvent,
  type GoalBar,
  type Match,
  type Score,
} from "@/types/Game";

const API_URL = import.meta.env.VITE_API_URL;

type TeamPlayers = {
  blue: PlayerAssignment[];
  red: PlayerAssignment[];
};

/**
 * The live match lives here rather than in GamePlay's useState, because
 * goals now arrive from three places - the buttons, the camera over a
 * websocket, and a page reload re-fetching the match - and all three have
 * to converge on the same list.
 *
 * The score is never incremented locally. Every write returns the score
 * derived from the goal log on the server, and we take that. There is no
 * running counter here that could drift out of step with the events.
 */
interface GameState extends TeamPlayers {
  matchId: number | null;
  status: "idle" | "starting" | "in_progress" | "finishing" | "failed";
  events: GoalEvent[];
  score: Score;
  error: string | null;
  /** Camera goals nobody has confirmed or corrected yet. */
  cameraConnected: boolean;
}

const initialState: GameState = {
  blue: [],
  red: [],
  matchId: null,
  status: "idle",
  events: [],
  score: { blue: 0, red: 0 },
  error: null,
  cameraConnected: false,
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      /* body was not json - keep the status message */
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

// ---------------------------------------------------------------
// thunks
// ---------------------------------------------------------------

/** Called when the four players are picked, BEFORE any play happens.
 *  This is what gives the vision service something to attach to. */
export const startMatch = createAsyncThunk(
  "game/startMatch",
  async (players: TeamPlayers) => {
    const blueOffense = players.blue.find((p) => p.position === "offense")!;
    const blueDefense = players.blue.find((p) => p.position === "defense")!;
    const redOffense = players.red.find((p) => p.position === "offense")!;
    const redDefense = players.red.find((p) => p.position === "defense")!;

    const match = await request<Match>("/matches/start", {
      method: "POST",
      body: JSON.stringify({
        player1_id: blueOffense.id,
        player2_id: blueDefense.id,
        player3_id: redOffense.id,
        player4_id: redDefense.id,
      }),
    });
    return { match, players };
  }
);

/** Re-load an in-progress match. Called on GamePlay mount so a browser
 *  refresh - or a second device - shows the true current state. */
export const loadMatch = createAsyncThunk(
  "game/loadMatch",
  async (matchId: number) => request<Match>(`/matches/${matchId}`)
);

export const recordGoal = createAsyncThunk(
  "game/recordGoal",
  async (goal: {
    matchId: number;
    team: "blue" | "red";
    playerId: number;
    bar: GoalBar;
    ownGoal: boolean;
  }) =>
    request<{ event: GoalEvent; score: Score }>(
      `/matches/${goal.matchId}/events`,
      {
        method: "POST",
        body: JSON.stringify({
          team: goal.team,
          player_id: goal.playerId,
          bar: goal.bar,
          own_goal: goal.ownGoal,
          source: "manual",
        }),
      }
    )
);

/** Confirm or correct a goal - the human half of assisted mode. */
export const updateGoal = createAsyncThunk(
  "game/updateGoal",
  async (payload: {
    matchId: number;
    eventId: number;
    changes: Partial<
      Pick<GoalEvent, "team" | "player_id" | "bar" | "own_goal" | "status">
    >;
  }) =>
    request<{ event: GoalEvent; score: Score }>(
      `/matches/${payload.matchId}/events/${payload.eventId}`,
      { method: "PATCH", body: JSON.stringify(payload.changes) }
    )
);

/** Hard delete - the Rewind button. Prefer rejecting a camera goal
 *  (updateGoal with status "rejected"): that keeps the record that the
 *  model got it wrong, which is the signal worth having. */
export const deleteGoal = createAsyncThunk(
  "game/deleteGoal",
  async (payload: { matchId: number; eventId: number }) => {
    const score = await request<Score>(
      `/matches/${payload.matchId}/events/${payload.eventId}`,
      { method: "DELETE" }
    );
    return { eventId: payload.eventId, score };
  }
);

/** Is there a game already in progress? Returns it, or null. */
export const fetchActiveMatch = createAsyncThunk(
  "game/fetchActiveMatch",
  async () => request<Match | null>("/matches/active")
);

/**
 * Recover from an abandoned browser tab.
 *
 * A match stays in_progress until somebody finishes it, so closing the
 * tab mid-game leaves one stranded and every later "Start Game" fails.
 * This picks that match back up: it re-reads the roster from the match's
 * player ids so the game continues with the right people on the right
 * sides, even in a fresh browser session with an empty Redux store.
 */
export const resumeActiveMatch = createAsyncThunk(
  "game/resumeActiveMatch",
  async (users: { id: number; name: string }[]) => {
    const match = await request<Match | null>("/matches/active");
    if (!match) throw new Error("There is no game in progress to resume");

    const nameOf = (id: number) =>
      users.find((u) => u.id === id)?.name ?? `Player ${id}`;
    const assign = (
      id: number,
      position: "offense" | "defense"
    ): PlayerAssignment => ({ id, name: nameOf(id), position });

    return {
      match,
      players: {
        blue: [
          assign(match.player1_id, "offense"),
          assign(match.player2_id, "defense"),
        ],
        red: [
          assign(match.player3_id, "offense"),
          assign(match.player4_id, "defense"),
        ],
      },
    };
  }
);

/** Throw away a stranded match so a new one can start. The goals stay in
 *  the database and the video stays on disk - only the stat rollup is
 *  skipped, because a half-played game is not a result. */
export const abandonMatch = createAsyncThunk(
  "game/abandonMatch",
  async (matchId: number) =>
    request<Match>(`/matches/${matchId}/finish`, {
      method: "POST",
      body: JSON.stringify({ abandoned: true }),
    })
);

export const finishMatch = createAsyncThunk(
  "game/finishMatch",
  async (payload: { matchId: number; abandoned?: boolean }) =>
    request<Match>(`/matches/${payload.matchId}/finish`, {
      method: "POST",
      body: JSON.stringify({ abandoned: payload.abandoned ?? false }),
    })
);

// ---------------------------------------------------------------
// slice
// ---------------------------------------------------------------

function upsert(events: GoalEvent[], incoming: GoalEvent): GoalEvent[] {
  const index = events.findIndex((e) => e.id === incoming.id);
  if (index === -1) return [...events, incoming];
  const next = [...events];
  next[index] = incoming;
  return next;
}

const gameSlice = createSlice({
  name: "game",
  initialState,
  reducers: {
    setPlayers(state, action: PayloadAction<TeamPlayers>) {
      state.blue = action.payload.blue;
      state.red = action.payload.red;
    },

    /** Positions swap mid-game; team membership does not. */
    swapPositions(state, action: PayloadAction<"blue" | "red">) {
      state[action.payload] = state[action.payload].map((player) => ({
        ...player,
        position: player.position === "offense" ? "defense" : "offense",
      }));
    },

    /** A goal arrived over the websocket - from the camera, or from
     *  someone tapping on another device. */
    goalReceived(
      state,
      action: PayloadAction<{ event: GoalEvent; score: Score }>
    ) {
      state.events = upsert(state.events, action.payload.event);
      state.score = action.payload.score;
    },

    goalRemoved(
      state,
      action: PayloadAction<{ eventId: number; score: Score }>
    ) {
      state.events = state.events.filter((e) => e.id !== action.payload.eventId);
      state.score = action.payload.score;
    },

    setCameraConnected(state, action: PayloadAction<boolean>) {
      state.cameraConnected = action.payload;
    },

    clearGame() {
      return { ...initialState };
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(startMatch.pending, (state) => {
        state.status = "starting";
        state.error = null;
      })
      .addCase(startMatch.fulfilled, (state, action) => {
        state.status = "in_progress";
        state.matchId = action.payload.match.id;
        state.blue = action.payload.players.blue;
        state.red = action.payload.players.red;
        state.events = [];
        state.score = { blue: 0, red: 0 };
      })
      .addCase(startMatch.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message ?? "Could not start the match";
      })

      .addCase(resumeActiveMatch.fulfilled, (state, action) => {
        state.status = "in_progress";
        state.error = null;
        state.matchId = action.payload.match.id;
        state.blue = action.payload.players.blue;
        state.red = action.payload.players.red;
        state.events = action.payload.match.goal_events ?? [];
        state.score = {
          blue: action.payload.match.score_blue,
          red: action.payload.match.score_red,
        };
      })
      .addCase(abandonMatch.fulfilled, () => ({ ...initialState }))

      .addCase(loadMatch.fulfilled, (state, action) => {
        state.matchId = action.payload.id;
        state.events = action.payload.goal_events ?? [];
        state.score = {
          blue: action.payload.score_blue,
          red: action.payload.score_red,
        };
        state.status =
          action.payload.status === "in_progress" ? "in_progress" : "idle";
      })

      .addCase(recordGoal.fulfilled, (state, action) => {
        state.events = upsert(state.events, action.payload.event);
        state.score = action.payload.score;
      })
      .addCase(updateGoal.fulfilled, (state, action) => {
        state.events = upsert(state.events, action.payload.event);
        state.score = action.payload.score;
      })
      .addCase(deleteGoal.fulfilled, (state, action) => {
        state.events = state.events.filter(
          (e) => e.id !== action.payload.eventId
        );
        state.score = action.payload.score;
      })

      .addCase(finishMatch.pending, (state) => {
        state.status = "finishing";
      })
      .addCase(finishMatch.fulfilled, () => ({ ...initialState }))
      .addCase(finishMatch.rejected, (state, action) => {
        state.status = "in_progress";
        state.error = action.error.message ?? "Could not save the match";
      })

      // Any failed write leaves the server as the authority - surface the
      // error rather than pretending the local state is right.
      .addMatcher(
        (action) =>
          action.type.startsWith("game/") && action.type.endsWith("/rejected"),
        (state, action: any) => {
          state.error = action.error?.message ?? "Something went wrong";
        }
      );
  },
});

export const {
  setPlayers,
  swapPositions,
  goalReceived,
  goalRemoved,
  setCameraConnected,
  clearGame,
} = gameSlice.actions;
export default gameSlice.reducer;
