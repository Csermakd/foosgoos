import { Button } from "@/components/ui/button";

import { type PlayerAssignment, type GoalBar } from "@/types/Game";

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

type GoalButton = {
  label: string;

  value: GoalType;
};

const GOAL_BUTTONS: {
  offense: GoalButton[];

  defense: GoalButton[];
} = {
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

const PlayerCard = ({ player, teamIcon, stats, onGoal }: PlayerCardProps) => {
  // Safety check: defaults to offense buttons if position is somehow undefined
  const buttons = GOAL_BUTTONS[player.position] || GOAL_BUTTONS["offense"];

  return (
    <div className="flex flex-col items-center gap-4 p-4 bg-white/50 rounded-lg shadow-md w-full max-w-xs">
      {/* Player Info */}

      <img src={teamIcon} alt={player.position} className="w-10 h-10" />

      <div className="text-center">
        <p className="text-lg font-bold">{player.name}</p>
        <p className="text-sm capitalize text-muted-foreground">
          {player.position}
        </p>
      </div>

      {/* Player Stats */}

      <div className="text-left w-full px-2">
        {/* Main stats in a 2-column grid */}

        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          {ALL_GOAL_TYPES.map((goalType) => (
            <div
              key={goalType.value}
              className="flex justify-between text-sm col-span-1" // Each item takes one column
            >
              <span className="text-muted-foreground">{goalType.label}:</span>

              <span className="font-semibold">
                {stats[goalType.value] || 0}
              </span>
            </div>
          ))}
        </div>

        {/* Show Own Goals separately, centered in the third row */}

        {stats.ownGoal > 0 && (
          <div className="flex justify-center text-sm mt-2 col-span-2">
            {" "}
            {/* Spans both columns, centered */}
            <span className="text-red-500 mr-1">Own Goals:</span>
            <span className="font-semibold text-red-500">{stats.ownGoal}</span>
          </div>
        )}
      </div>

      {/* Goal Buttons */}

      <div className="flex flex-col w-full gap-2">
        {buttons.map((button) => (
          <Button
            key={button.value}
            variant="neutral"
            className={cn(button.value === "ownGoal" ? "text-red-500" : "")}
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
