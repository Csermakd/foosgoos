import { useEffect, useMemo, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { type RootState, type AppDispatch } from "@/store";
import { type GoalBar, type GoalEvent } from "@/types/Game";
import {
  recordGoal,
  updateGoal,
  deleteGoal,
  finishMatch,
  loadMatch,
  swapPositions,
} from "@/features/game/gameSlice";
import { useMatchSocket } from "@/hooks/useMatchSocket";
import { Button } from "@/components/ui/button";
import PlayerCard from "@/components/PlayerCard";
import GoalReview from "@/components/GoalReview";

import FooseballTable from "../assets/foosball_table.svg";
import BlueTeamIcon from "../assets/blue_player.svg";
import RedTeamIcon from "../assets/red_player.svg";
import SwitchIcon from "../pixel_assets/buttons/switch_arrow_black.png";

type PlayerGoalStats = {
  "5bar": number;
  "3bar": number;
  goalie: number;
  "2bar": number;
  ownGoal: number;
};

const emptyStats = (): PlayerGoalStats => ({
  "5bar": 0,
  "3bar": 0,
  goalie: 0,
  "2bar": 0,
  ownGoal: 0,
});

const GamePlay = () => {
  const dispatch: AppDispatch = useDispatch();
  const navigate = useNavigate();

  const { blue, red, matchId, events, score, error, cameraConnected } =
    useSelector((state: RootState) => state.game);

  // Camera goals a human has explicitly skipped this session. They stay
  // in the log (and on the scoreboard) - we just stop asking about them.
  const [dismissed, setDismissed] = useState<number[]>([]);

  useMatchSocket(matchId);

  // A browser refresh mid-game used to lose everything, because the score
  // lived in useState. Now the match is on the server, so re-fetch it.
  useEffect(() => {
    if (matchId !== null && events.length === 0) {
      dispatch(loadMatch(matchId));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matchId]);

  const blueDefense = blue.find((p) => p.position === "defense");
  const blueOffense = blue.find((p) => p.position === "offense");
  const redDefense = red.find((p) => p.position === "defense");
  const redOffense = red.find((p) => p.position === "offense");

  /** Per-player tallies, derived from the goal log rather than tracked
   *  alongside it - so corrections and undos are automatically reflected. */
  const playerGoals = useMemo(() => {
    const table: Record<number, PlayerGoalStats> = {};
    for (const event of events) {
      if (event.status === "rejected" || event.player_id === null) continue;
      const stats = (table[event.player_id] ??= emptyStats());
      if (event.own_goal) stats.ownGoal += 1;
      else if (event.bar !== "unknown") stats[event.bar] += 1;
    }
    return table;
  }, [events]);

  /** Camera goals still waiting on "who scored?". */
  const needsReview: GoalEvent[] = useMemo(
    () =>
      events.filter(
        (e) =>
          e.source === "camera" &&
          e.status === "pending_review" &&
          !dismissed.includes(e.id)
      ),
    [events, dismissed]
  );
  const reviewing = needsReview[0];

  const handleGoalRecord = (
    playerId: number,
    _position: "offense" | "defense",
    goalType: GoalBar | "ownGoal"
  ) => {
    if (matchId === null) return;
    const team = blue.some((p) => p.id === playerId) ? "blue" : "red";
    const ownGoal = goalType === "ownGoal";
    dispatch(
      recordGoal({
        matchId,
        // An own goal puts the point on the OTHER team's board, but stays
        // attributed to the player who scored it.
        team: ownGoal ? (team === "blue" ? "red" : "blue") : team,
        playerId,
        bar: ownGoal ? "unknown" : (goalType as GoalBar),
        ownGoal,
      })
    );
  };

  const handleRewind = () => {
    if (matchId === null || events.length === 0) return;
    const last = events[events.length - 1];
    dispatch(deleteGoal({ matchId, eventId: last.id }));
  };

  const handleFinish = async () => {
    if (matchId === null) return;
    if (needsReview.length > 0) {
      const proceed = window.confirm(
        `${needsReview.length} goal(s) the camera detected have not been ` +
          `attributed to a player. They will count towards the team score ` +
          `but not towards anyone's personal stats. Finish anyway?`
      );
      if (!proceed) return;
    }
    try {
      const match = await dispatch(finishMatch({ matchId })).unwrap();
      alert(
        `Match saved. ${match.score_blue}-${match.score_red}, ` +
          `winner: ${match.winner_team.toUpperCase()}`
      );
      navigate("/");
    } catch (err: any) {
      alert(`Could not save the match: ${err.message}`);
    }
  };

  if (matchId === null || !blueDefense || !blueOffense || !redDefense || !redOffense) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-red-500 font-bold">
          No match in progress. Start one from the Create Game screen.
        </p>
        <Button onClick={() => navigate("/create-game")}>Start a game</Button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen w-screen gap-8 bg-gray-700 p-8">
      {/* Blue Team */}
      <div className="flex flex-col items-center gap-8 flex-1">
        <h2 className="text-4xl font-black text-blue-400 drop-shadow-md">
          {score.blue}
        </h2>
        <PlayerCard
          player={blueDefense}
          teamIcon={BlueTeamIcon}
          stats={playerGoals[blueDefense.id] ?? emptyStats()}
          onGoal={handleGoalRecord}
        />
        <Button
          variant="neutral"
          size="icon"
          onClick={() => dispatch(swapPositions("blue"))}
        >
          <img src={SwitchIcon} alt="Switch Blue Team" className="w-6 h-6" />
        </Button>
        <PlayerCard
          player={blueOffense}
          teamIcon={BlueTeamIcon}
          stats={playerGoals[blueOffense.id] ?? emptyStats()}
          onGoal={handleGoalRecord}
        />
      </div>

      {/* Center */}
      <div className="flex flex-col items-center justify-center flex-2">
        <div className="flex items-center gap-2 mb-2 text-xs font-bold uppercase tracking-wide">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              cameraConnected ? "bg-green-400" : "bg-gray-400"
            }`}
          />
          <span className="text-white/80">
            {cameraConnected ? "Live — camera assisted" : "Manual only"}
          </span>
        </div>

        <img
          src={FooseballTable}
          alt="Foosball Table"
          className="w-full max-w-xl h-auto drop-shadow-2xl"
        />

        {error && (
          <p className="mt-4 text-sm font-bold text-red-300">{error}</p>
        )}

        <div className="flex gap-4 mt-8 w-full max-w-xl">
          <Button
            onClick={handleRewind}
            disabled={events.length === 0}
            className="flex-1"
            variant="neutral"
          >
            Rewind
          </Button>
          <Button
            onClick={handleFinish}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white border-none"
          >
            Finish Match
          </Button>
        </div>
      </div>

      {/* Red Team */}
      <div className="flex flex-col items-center gap-8 flex-1">
        <h2 className="text-4xl font-black text-red-400 drop-shadow-md">
          {score.red}
        </h2>
        <PlayerCard
          player={redOffense}
          teamIcon={RedTeamIcon}
          stats={playerGoals[redOffense.id] ?? emptyStats()}
          onGoal={handleGoalRecord}
        />
        <Button
          variant="neutral"
          size="icon"
          onClick={() => dispatch(swapPositions("red"))}
        >
          <img src={SwitchIcon} alt="Switch Red Team" className="w-6 h-6" />
        </Button>
        <PlayerCard
          player={redDefense}
          teamIcon={RedTeamIcon}
          stats={playerGoals[redDefense.id] ?? emptyStats()}
          onGoal={handleGoalRecord}
        />
      </div>

      {reviewing && (
        <GoalReview
          event={reviewing}
          roster={{ blue, red }}
          onAssign={(playerId, bar) =>
            dispatch(
              updateGoal({
                matchId,
                eventId: reviewing.id,
                changes: { player_id: playerId, bar, status: "confirmed" },
              })
            )
          }
          onReject={() =>
            dispatch(
              updateGoal({
                matchId,
                eventId: reviewing.id,
                changes: { status: "rejected" },
              })
            )
          }
          onDismiss={() => setDismissed((prev) => [...prev, reviewing.id])}
        />
      )}
    </div>
  );
};

export default GamePlay;
