import { useEffect, useMemo, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/input";
import { StatList, type Stat } from "@/components/ui/StatList";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { PixelImg } from "@/components/ui/PixelImg";
import PageShell from "@/components/layout/PageShell";
import { sprites } from "@/pixel_assets/sprites";
import { type AppDispatch, type RootState } from "@/store";
import { fetchAllUsers } from "@/features/user/userSlice";
import { type User } from "@/types/Game";


const ViewUser = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<User | null>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  const dispatch: AppDispatch = useDispatch();
  const { users: allUsers, status } = useSelector(
    (state: RootState) => state.users
  );

  // Landing here directly (a refresh, a bookmark) used to show an empty
  // picker, because only the home screen ever fetched the roster.
  useEffect(() => {
    if (status === "idle") dispatch(fetchAllUsers());
  }, [dispatch, status]);

  useEffect(() => {
    if (!isOpen) return;
    const onPointerDown = (e: MouseEvent) => {
      if (!searchRef.current?.contains(e.target as Node)) setIsOpen(false);
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [isOpen]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allUsers;
    return allUsers.filter((p) => p.name.toLowerCase().includes(q));
  }, [query, allUsers]);

  function choosePlayer(p: User) {
    setSelected(p);
    setIsOpen(false);
    setQuery("");
    // NOTE: In the future, dispatch an action here to fetch specific stats
    // for this user from the backend API (/stats/users?username=...)
  }

  const stats: Stat[] = [
    { label: "Total goals", value: selected?.stats?.goals ?? 0 },
    { label: "Saves", value: selected?.stats?.saves ?? 0 },
    { label: "Offense goals", value: selected?.stats?.goals_from_offense ?? 0 },
    { label: "Defense goals", value: selected?.stats?.goals_from_defense ?? 0 },
    { label: "Matches played", value: selected?.stats?.matches_played ?? 0 },
    { label: "Matches won", value: selected?.stats?.matches_won ?? 0 },
    {
      label: "Own goals",
      value: selected?.stats?.own_goals ?? 0,
      tone: "danger",
    },
  ];

  const searchBox = (
    <div className="relative" ref={searchRef}>
      <Button variant="neutral" onClick={() => setIsOpen((s) => !s)}>
        <PixelIcon name="search" />
        {selected ? selected.name : "Search player"}
        <PixelIcon name="chevronDown" />
      </Button>

      {isOpen && (
        <Card className="absolute right-0 z-50 mt-2 w-72 gap-3 p-3">
          <Input
            placeholder="Type a player name..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          <ul className="max-h-56 overflow-auto">
            {filtered.map((p) => (
              <li key={p.id}>
                <button
                  type="button"
                  className="w-full rounded-base border-2 border-transparent px-3 py-2 text-left text-sm hover:border-border hover:bg-sunken"
                  onClick={() => choosePlayer(p)}
                >
                  {p.name}
                </button>
              </li>
            ))}
            {filtered.length === 0 && (
              <li className="px-3 py-2 text-sm text-muted-foreground">
                No players found
              </li>
            )}
          </ul>
        </Card>
      )}
    </div>
  );

  return (
    <PageShell
      title="Player Profile"
      icon={sprites.bluePlayerTorso}
      width="wide"
      action={searchBox}
    >
      <Card className="mx-auto max-w-lg items-center p-6 sm:p-8">
        <PixelImg src={sprites.bluePlayer} outlined className="h-56 w-auto" />

        <h2 className="text-center font-display text-base sm:text-lg">
          {selected ? selected.name : "No player selected"}
        </h2>

        {selected ? (
          <StatList stats={stats} className="w-full" />
        ) : (
          <p className="rounded-base border-2 border-border bg-sunken px-4 py-6 text-center text-sm text-muted-foreground">
            Pick a player with the search button above to see their record.
          </p>
        )}
      </Card>
    </PageShell>
  );
};

export default ViewUser;
