import { useEffect, useMemo } from "react";
import { useSelector, useDispatch } from "react-redux";

import { Badge } from "@/components/ui/badge";
import { PixelImg } from "@/components/ui/PixelImg";
import PageShell from "@/components/layout/PageShell";
import { type RootState, type AppDispatch } from "@/store";
import { fetchAllUsers } from "@/features/user/userSlice";
import { sprites } from "@/pixel_assets/sprites";
import { cn } from "@/lib/utils";

/**
 * Podium styling, keyed off the finishing position.
 *
 * There is only one trophy sprite in `pixel_assets`, so silver and bronze are
 * derived from it with a filter rather than by asking for two more drawings.
 * Hue-rotate keeps the pixel edges perfectly crisp - it recolours, it does not
 * resample.
 */
const PODIUM = [
  { row: "bg-gold-soft", badge: "gold", filter: undefined },
  {
    // Darkened, not lightened: the silver row is already near-white, so a
    // brightened trophy vanished into it.
    row: "bg-silver-soft",
    badge: "silver",
    filter: "grayscale(1) brightness(0.78) contrast(1.15)",
  },
  {
    // `sepia` first flattens the gold to a neutral brown that hue-rotate can
    // actually steer; rotating the raw yellow barely moved it off gold.
    row: "bg-bronze-soft",
    badge: "bronze",
    filter: "sepia(1) saturate(3.2) hue-rotate(-18deg) brightness(0.72)",
  },
] as const;

const LeaderBoards = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { users, status } = useSelector((state: RootState) => state.users);

  // Force a data refresh when page loads to ensure stats are up-to-date
  useEffect(() => {
    dispatch(fetchAllUsers());
  }, [dispatch]);

  // Sort users by Total Goals (Highest first)
  const sortedUsers = useMemo(() => {
    return [...users].sort(
      (a, b) => (b.stats?.goals || 0) - (a.stats?.goals || 0)
    );
  }, [users]);

  return (
    <PageShell
      title="Leaderboard"
      subtitle="Ranked by total goals scored."
      icon={sprites.trophy}
      width="regular"
    >
      {status === "loading" ? (
        <p className="py-10 text-center text-muted-foreground">
          Updating scores...
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-12 gap-4 px-4 text-sm font-heading uppercase tracking-wide text-muted-foreground">
            <div className="col-span-3">Rank</div>
            <div className="col-span-5">Player</div>
            <div className="col-span-4 text-right">Goals</div>
          </div>

          {sortedUsers.map((user, index) => {
            const podium = PODIUM[index];
            return (
              <div
                key={user.id}
                className={cn(
                  "grid grid-cols-12 items-center gap-4 rounded-base border-2 border-border px-4 py-3 shadow-shadow",
                  podium ? podium.row : "bg-secondary-background"
                )}
              >
                <div className="col-span-3 flex items-center gap-2">
                  {podium ? (
                    <>
                      <PixelImg
                        src={sprites.trophy}
                        alt={`Rank ${index + 1} trophy`}
                        className="h-8 w-auto"
                        style={{ filter: podium.filter }}
                      />
                      <Badge variant={podium.badge}>#{index + 1}</Badge>
                    </>
                  ) : (
                    <span className="pl-1 font-heading text-muted-foreground">
                      #{index + 1}
                    </span>
                  )}
                </div>

                <div className="col-span-5 flex items-center gap-2">
                  <PixelImg
                    src={sprites.bluePlayerTorso}
                    outlined
                    className="h-8 w-auto shrink-0"
                  />
                  <span className="truncate font-heading text-lg">
                    {user.name}
                  </span>
                </div>

                <div className="col-span-4 text-right">
                  <span className="font-display text-xl tabular-nums">
                    {user.stats?.goals || 0}
                  </span>
                </div>
              </div>
            );
          })}

          {sortedUsers.length === 0 && (
            <div className="flex flex-col items-center gap-3 rounded-base border-2 border-border bg-sunken py-10 text-center text-muted-foreground">
              <PixelImg src={sprites.trophy} className="h-14 w-auto opacity-40" />
              No players yet. Create some users to get started.
            </div>
          )}
        </div>
      )}
    </PageShell>
  );
};

export default LeaderBoards;
