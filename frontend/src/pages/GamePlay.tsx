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
import PageShell from "@/components/layout/PageShell";
import MatchLayout from "@/components/layout/MatchLayout";
import TableImage from "@/components/TableImage";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { sprites } from "@/pixel_assets/sprites";
import { cn } from "@/lib/utils";

import BlueTeamIcon from "../assets/blue_player.svg";
import RedTeamIcon from "../assets/red_player.svg";

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

/** The one place a team colour runs at full saturation - it makes the score
 *  the loudest thing on the screen, which is the point of the screen. */
const ScoreTile = ({ team, score }: { team: "blue" | "red"; score: number }) => (
  <div
    className={cn(
      "flex w-full max-w-xs items-center justify-between rounded-base border-2 border-border px-4 py-3 shadow-shadow",
      team === "blue" ? "bg-blue-team" : "bg-red-team"
    )}
  >
    <span className="font-heading uppercase tracking-wide text-main-foreground">
      {team}
    </span>
    <span className="font-display text-3xl leading-none tabular-nums text-main-foreground">
      {score}
    </span>
  </div>
);

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

  if (
    matchId === null ||
    !blueDefense ||
    !blueOffense ||
    !redDefense ||
    !redOffense
  ) {
    return (
      <PageShell title="Live Match" icon={sprites.table} width="regular">
        <div className="flex flex-col items-center gap-4 rounded-base border-2 border-border bg-sunken px-6 py-12 text-center">
          <p className="font-heading">No match in progress.</p>
          <p className="text-sm text-muted-foreground">
            Pick four players to get a game going.
          </p>
          <Button onClick={() => navigate("/create-game")}>Start a game</Button>
        </div>
      </PageShell>
    );
  }

  const cameraStatus = (
    <div className="flex items-center gap-2 rounded-base border-2 border-border bg-secondary-background px-3 py-2 text-sm font-heading uppercase tracking-wide">
      <span
        className={cn(
          "inline-block size-2.5 rounded-full border-2 border-border",
          cameraConnected ? "bg-success" : "bg-muted-foreground"
        )}
      />
      {cameraConnected ? "Live · camera assisted" : "Manual only"}
    </div>
  );

  return (
    <PageShell
      title="Live Match"
      icon={sprites.table}
      width="full"
      action={cameraStatus}
    >
      <MatchLayout
        blue={
          <>
            <ScoreTile team="blue" score={score.blue} />
            <PlayerCard
              player={blueDefense}
              team="blue"
              teamIcon={BlueTeamIcon}
              stats={playerGoals[blueDefense.id] ?? emptyStats()}
              onGoal={handleGoalRecord}
            />
            <Button
              variant="neutral"
              size="sm"
              onClick={() => dispatch(swapPositions("blue"))}
            >
              <PixelIcon name="swap" />
              Swap positions
            </Button>
            <PlayerCard
              player={blueOffense}
              team="blue"
              teamIcon={BlueTeamIcon}
              stats={playerGoals[blueOffense.id] ?? emptyStats()}
              onGoal={handleGoalRecord}
            />
          </>
        }
        center={
          <>
            <TableImage />

            {error && (
              <p className="w-full max-w-xl rounded-base border-2 border-border bg-danger-soft px-3 py-2 text-center text-sm font-heading">
                {error}
              </p>
            )}

            <div className="flex w-full max-w-xl flex-col gap-4 sm:flex-row">
              <Button
                onClick={handleRewind}
                disabled={events.length === 0}
                className="flex-1"
                size="lg"
                variant="neutral"
              >
                Rewind
              </Button>
              <Button
                onClick={handleFinish}
                className="flex-1"
                size="lg"
                variant="success"
              >
                Finish Match
              </Button>
            </div>
          </>
        }
        red={
          <>
            <ScoreTile team="red" score={score.red} />
            <PlayerCard
              player={redOffense}
              team="red"
              teamIcon={RedTeamIcon}
              stats={playerGoals[redOffense.id] ?? emptyStats()}
              onGoal={handleGoalRecord}
            />
            <Button
              variant="neutral"
              size="sm"
              onClick={() => dispatch(swapPositions("red"))}
            >
              <PixelIcon name="swap" />
              Swap positions
            </Button>
            <PlayerCard
              player={redDefense}
              team="red"
              teamIcon={RedTeamIcon}
              stats={playerGoals[redDefense.id] ?? emptyStats()}
              onGoal={handleGoalRecord}
            />
          </>
        }
      />

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
    </PageShell>
  );
};

export default GamePlay;
