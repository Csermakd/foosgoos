import { useMemo } from "react";
import { Button } from "@/components/ui/button";
import {
  type GoalEvent,
  type GoalBar,
  type PlayerAssignment,
} from "@/types/Game";

const BARS: { label: string; value: GoalBar }[] = [
  { label: "5 Bar", value: "5bar" },
  { label: "3 Bar", value: "3bar" },
  { label: "2 Bar", value: "2bar" },
  { label: "Goalie", value: "goalie" },
];

type Props = {
  event: GoalEvent;
  roster: { blue: PlayerAssignment[]; red: PlayerAssignment[] };
  onAssign: (playerId: number, bar: GoalBar) => void;
  onReject: () => void;
  onDismiss: () => void;
};

/**
 * The whole point of "assisted" mode.
 *
 * The camera has already put the point on the board - the score is right
 * whether or not anyone touches this. What is missing is WHO scored and
 * off which rod, which the camera genuinely cannot know. So this asks for
 * exactly that, in one tap, and offers "not a goal" for when the camera
 * was simply wrong.
 *
 * It deliberately does not block or auto-dismiss on a timer: a goal that
 * scrolls away unattributed is a goal missing from someone's stats, and
 * people are looking at the table, not the tablet.
 */
const GoalReview = ({ event, roster, onAssign, onReject, onDismiss }: Props) => {
  const scoringTeam = event.team;
  const candidates = useMemo(
    () => (scoringTeam === "blue" ? roster.blue : roster.red),
    [scoringTeam, roster]
  );

  const accent =
    scoringTeam === "blue"
      ? "border-blue-400 bg-blue-50"
      : "border-red-400 bg-red-50";

  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-[min(94vw,44rem)]
                  rounded-lg border-4 ${accent} shadow-2xl p-4`}
      role="dialog"
      aria-label="Confirm the goal the camera detected"
    >
      <div className="flex items-baseline justify-between gap-4">
        <p className="text-lg font-black uppercase">
          Camera saw a {scoringTeam} goal
        </p>
        <p className="text-xs text-muted-foreground">
          {event.detector_note ?? "camera"}
          {event.confidence !== null
            ? ` · ${Math.round(event.confidence * 100)}% sure`
            : ""}
        </p>
      </div>
      <p className="text-sm text-muted-foreground mb-3">
        Already counted. Who scored it?
      </p>

      <div className="flex flex-col gap-2">
        {candidates.map((player) => (
          <div key={player.id} className="flex items-center gap-2">
            <span className="w-32 shrink-0 font-bold truncate">
              {player.name}
            </span>
            <span className="w-20 shrink-0 text-xs capitalize text-muted-foreground">
              {player.position}
            </span>
            <div className="flex gap-1 flex-wrap">
              {BARS.map((bar) => (
                <Button
                  key={bar.value}
                  size="sm"
                  variant="neutral"
                  onClick={() => onAssign(player.id, bar.value)}
                >
                  {bar.label}
                </Button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 mt-4">
        <Button
          variant="neutral"
          className="flex-1 text-red-600"
          onClick={onReject}
        >
          Not a goal — take the point back
        </Button>
        <Button variant="neutral" className="flex-1" onClick={onDismiss}>
          Skip (leave unattributed)
        </Button>
      </div>
    </div>
  );
};

export default GoalReview;
