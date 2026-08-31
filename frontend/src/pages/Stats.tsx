import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { Badge } from "@/components/ui/badge";
import { PixelImg } from "@/components/ui/PixelImg";
import PageShell from "@/components/layout/PageShell";
import { sprites } from "@/pixel_assets/sprites";
import { fetchAllUsers } from "@/features/user/userSlice";
import { type AppDispatch, type RootState } from "@/store";
import { type Match } from "@/types/Game";
import { cn } from "@/lib/utils";

type TeamSide = {
  label: string;
  score: number;
  offense: string;
  defense: string;
  won: boolean;
  tone: "blue" | "red";
};

const TeamColumn = ({ label, score, offense, defense, won, tone }: TeamSide) => (
  <div className="flex-1 text-center">
    <Badge variant={tone}>{label}</Badge>
    <div className="my-2 flex items-center justify-center gap-3">
      <PixelImg
        src={tone === "blue" ? sprites.bluePlayerTorso : sprites.redPlayerTorso}
        outlined
        className={cn("h-10 w-auto", !won && "opacity-45")}
      />
      <span
        className={cn(
          "font-display text-3xl tabular-nums",
          won ? "text-foreground" : "text-muted-foreground"
        )}
      >
        {score}
      </span>
    </div>
    <div className="flex flex-col gap-0.5 text-sm text-muted-foreground">
      <span>
        Offense <span className="font-heading text-foreground">{offense}</span>
      </span>
      <span>
        Defense <span className="font-heading text-foreground">{defense}</span>
      </span>
    </div>
  </div>
);

const Stats = () => {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);

  // Get the list of users from Redux so we can translate IDs to Names.
  // Landing here directly - a refresh, a bookmark - used to render every
  // roster slot as "Unknown", because only the home screen fetched them.
  const dispatch: AppDispatch = useDispatch();
  const { users, status } = useSelector((state: RootState) => state.users);

  useEffect(() => {
    if (status === "idle") dispatch(fetchAllUsers());
  }, [dispatch, status]);

  const getName = (id: number) =>
    users.find((u) => u.id === id)?.name ?? "Unknown";

  useEffect(() => {
    const fetchMatches = async () => {
      try {
        // Only finished games. Matches now exist from the moment the
        // players are picked, so an unfiltered fetch would list the game
        // being played right now - and any abandoned one - as a result.
        const res = await fetch(
          `${import.meta.env.VITE_API_URL}/matches/?status=completed`
        );
        if (res.ok) {
          setMatches(await res.json());
        }
      } catch (error) {
        console.error("Failed to load matches", error);
      } finally {
        setLoading(false);
      }
    };
    fetchMatches();
  }, []);

  return (
    <PageShell
      title="Recent Matches"
      subtitle="Every completed game, newest first."
      icon={sprites.table}
      width="wide"
    >
      {loading ? (
        <p className="py-10 text-center text-muted-foreground">
          Loading match history...
        </p>
      ) : (
        <div className="grid gap-4">
          {matches.length === 0 && (
            <div className="flex flex-col items-center gap-3 rounded-base border-2 border-border bg-sunken py-10 text-center text-muted-foreground">
              <PixelImg src={sprites.table} className="h-16 w-auto opacity-40" />
              No matches recorded yet.
            </div>
          )}

          {matches.map((match) => (
            <div
              key={match.id}
              className="flex items-center justify-between rounded-base border-2 border-border bg-secondary-background p-4 shadow-shadow"
            >
              <TeamColumn
                label="Blue"
                tone="blue"
                score={match.score_blue}
                offense={getName(match.player1_id)}
                defense={getName(match.player2_id)}
                won={match.winner_team === "blue"}
              />

              <div className="flex flex-col items-center gap-2 px-4 sm:px-6">
                <span className="text-sm font-heading text-muted-foreground">
                  VS
                </span>
                <span className="text-xs text-muted-foreground">
                  {new Date(match.timestamp).toLocaleDateString()}
                </span>
                {match.winner_team !== "NONE" && (
                  <Badge variant={match.winner_team === "blue" ? "blue" : "red"}>
                    {match.winner_team} won
                  </Badge>
                )}
              </div>

              <TeamColumn
                label="Red"
                tone="red"
                score={match.score_red}
                offense={getName(match.player3_id)}
                defense={getName(match.player4_id)}
                won={match.winner_team === "red"}
              />
            </div>
          ))}
        </div>
      )}
    </PageShell>
  );
};

export default Stats;
