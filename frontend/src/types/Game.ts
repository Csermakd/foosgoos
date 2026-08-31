export type Team = {
  name: string;
  players: [Player, Player];
  score: number;
};

export type Player = {
  name: string;
  goals: {
    goalie: number;
    twoBar: number;
    threeBar: number;
    fiveBar: number;
    ownGoal: number;
  };
  record: {
    wins: number;
    losses: number;
  };
  position: "offense" | "defense";
};

export type PlayerAssignment = {
  id: number;
  name: string;
  position: "offense" | "defense";
};

export type GameResult = {
  winners: [string, string];
  losers: [string, string];
  date: string; // ISO string
};

/** The rods a goal can come off. "unknown" is a real answer, not a
 *  placeholder: the camera usually cannot tell which rod was involved,
 *  and saying so honestly is what prompts a human to fill it in. */
export type GoalBar = "5bar" | "3bar" | "2bar" | "goalie" | "unknown";

export type GoalSource = "manual" | "camera";

/** pending_review counts towards the score but has not been looked at by
 *  a person yet - the scoreboard stays right even if nobody is watching
 *  the tablet, and the UI highlights these for review. */
export type GoalStatus = "pending_review" | "confirmed" | "rejected";

/** One goal as stored by the backend. Mirrors schemas/goal_event_schema.py. */
export type GoalEvent = {
  id: number;
  match_id: number;
  event_uuid: string;
  created_at: string;
  video_ts_ms: number | null;
  team: "blue" | "red";
  player_id: number | null;
  bar: GoalBar;
  own_goal: boolean;
  source: GoalSource;
  status: GoalStatus;
  confidence: number | null;
  detector_note: string | null;
};

export type Score = { blue: number; red: number };

export type GoalEventResult = {
  event: GoalEvent;
  score: Score;
  duplicate: boolean;
};

export type MatchStatus = "in_progress" | "completed" | "abandoned";

export type Match = {
  id: number;
  timestamp: string;
  player1_id: number;
  player2_id: number;
  player3_id: number;
  player4_id: number;
  winner_team: "blue" | "red" | "NONE";
  score_blue: number;
  score_red: number;
  status: MatchStatus;
  started_at: string | null;
  ended_at: string | null;
  video_path: string | null;
  goal_events?: GoalEvent[];
};

/** Messages pushed over the match websocket. */
export type MatchSocketMessage =
  | ({ type: "goal_added" | "goal_updated" } & GoalEventResult)
  | { type: "goal_deleted"; event_id: number; score: Score }
  | {
      type: "match_finished";
      match_id: number;
      status: MatchStatus;
      score?: Score;
      winner_team?: string;
    };

export interface User {
  id: number;
  name: string;
  stats?: {
    goals: number;
    goals_from_offense: number;
    goals_from_defense: number;
    own_goals: number;
    saves: number;
    matches_played: number;
    matches_won: number;
  };
}
