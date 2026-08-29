import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { type PlayerAssignment, type GoalBar } from "@/types/Game";
import { PixelImg } from "@/components/ui/PixelImg";
import { cn } from "@/lib/utils";

type PlayerGoalStats = {
  "5bar": number;
  "3bar": number;
  goalie: number;
  "2bar": number;
  ownGoal: number;
};

/** The bars a human can attribute, plus own goals. */
type GoalType = keyof PlayerGoalStats;

type GoalButton = { label: string; value: GoalType };

const GOAL_BUTTONS: Record<"offense" | "defense", GoalButton[]> = {
  offense: [
    { label: "5 Bar", value: "5bar" },
    { label: "3 Bar", value: "3bar" },
    { label: "Own Goal", value: "ownGoal" },
  ],
  defense: [
    { label: "Goalie", value: "goalie" },
    { label: "2 Bar", value: "2bar" },
    { label: "Own Goal", value: "ownGoal" },
  ],
};

const ALL_GOAL_TYPES: { label: string; value: GoalType }[] = [
  { label: "5 Bar", value: "5bar" },
  { label: "3 Bar", value: "3bar" },
  { label: "Goalie", value: "goalie" },
  { label: "2 Bar", value: "2bar" },
];

type PlayerCardProps = {
  player: PlayerAssignment;
  team: "blue" | "red";
  teamIcon: string;
  stats: PlayerGoalStats;
  /** Identifies the scorer by id, not by name: two people can share a
   *  name, and the backend attributes goals by user id. */
  onGoal: (
    playerId: number,
    position: "offense" | "defense",
    goalType: GoalBar | "ownGoal"
  ) => void;
};

const PlayerCard = ({
  player,
  team,
  teamIcon,
  stats,
  onGoal,
}: PlayerCardProps) => {
  // Safety check: defaults to offense buttons if position is somehow undefined
  const buttons = GOAL_BUTTONS[player.position] || GOAL_BUTTONS.offense;

  return (
    <div className="w-full max-w-xs overflow-hidden rounded-base border-2 border-border bg-secondary-background shadow-shadow">
      {/* Team colour lives in the header band only. Tinting the whole card
          made the two rosters shout over the table between them. */}
      <div
        className={cn(
          "flex items-center gap-3 border-b-2 border-border px-4 py-3",
          team === "blue" ? "bg-blue-team-soft" : "bg-red-team-soft"
        )}
      >
      <PixelImg src={teamIcon} outlined className="h-8 w-8 shrink-0" />
        <div className="min-w-0">
          <p className="truncate font-heading text-lg leading-tight">{player.name}</p>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            {player.position}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 px-4 py-3">
        {ALL_GOAL_TYPES.map((goalType) => (
          <div key={goalType.value} className="flex justify-between text-sm">
            <span className="text-muted-foreground">{goalType.label}</span>
            <span className="font-heading tabular-nums">
              {stats[goalType.value] || 0}
            </span>
          </div>
        ))}

        {stats.ownGoal > 0 && (
          <div className="col-span-2 mt-1 flex justify-center">
            <Badge variant="red">Own goals {stats.ownGoal}</Badge>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2 border-t-2 border-border p-3">
        {buttons.map((button) => (
          <Button
            key={button.value}
            variant={button.value === "ownGoal" ? "danger" : "neutral"}
            onClick={() => onGoal(player.id, player.position, button.value)}
          >
            {button.label}
          </Button>
        ))}
      </div>
    </div>
  );
};

export default PlayerCard;
