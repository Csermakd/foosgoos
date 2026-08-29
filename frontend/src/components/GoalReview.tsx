import { useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  type GoalEvent,
  type GoalBar,
  type PlayerAssignment,
} from "@/types/Game";
import { cn } from "@/lib/utils";

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

  return (
    <div
      className="fixed bottom-6 left-1/2 z-50 w-[min(94vw,44rem)] -translate-x-1/2
                 overflow-hidden rounded-base border-2 border-border
                 bg-secondary-background shadow-shadow"
      role="dialog"
      aria-label="Confirm the goal the camera detected"
    >
      <div
        className={cn(
          "flex flex-wrap items-center justify-between gap-2 border-b-2 border-border px-4 py-3",
          scoringTeam === "blue" ? "bg-blue-team-soft" : "bg-red-team-soft"
        )}
      >
        <div className="flex items-center gap-2">
          <Badge variant={scoringTeam === "blue" ? "blue" : "red"}>
            {scoringTeam} goal
          </Badge>
          <p className="font-heading">Already counted. Who scored it?</p>
        </div>
        <p className="text-xs text-muted-foreground">
          {event.detector_note ?? "camera"}
          {event.confidence !== null
            ? ` · ${Math.round(event.confidence * 100)}% sure`
            : ""}
        </p>
      </div>

      <div className="flex flex-col gap-2 p-4">
        {candidates.map((player) => (
          <div
            key={player.id}
            className="flex flex-wrap items-center gap-2 rounded-base border-2 border-border bg-sunken px-3 py-2"
          >
            <span className="w-32 shrink-0 truncate font-heading">
              {player.name}
            </span>
            <span className="w-20 shrink-0 text-xs uppercase tracking-wide text-muted-foreground">
              {player.position}
            </span>
            <div className="flex flex-wrap gap-2">
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

      <div className="flex flex-col gap-2 border-t-2 border-border p-4 sm:flex-row">
        <Button variant="danger" className="flex-1" onClick={onReject}>
          Not a goal, take the point back
        </Button>
        <Button variant="neutral" className="flex-1" onClick={onDismiss}>
          Skip (leave unattributed)
        </Button>
      </div>
    </div>
  );
};

export default GoalReview;
