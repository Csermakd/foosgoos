import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";

import { Card } from "@/components/ui/Card";
import { PixelIcon, type PixelIconName } from "@/components/ui/PixelIcon";
import { PixelImg } from "@/components/ui/PixelImg";
import { type AppDispatch, type RootState } from "@/store";
import { fetchAllUsers } from "@/features/user/userSlice";
import { sprites } from "@/pixel_assets/sprites";

type MenuItem = {
  label: string;
  to: string;
  /** A sprite where the art exists, a drawn glyph where it does not. */
  sprite?: string;
  glyph?: PixelIconName;
  /** The primary action gets the accent; the rest stay neutral so there is
   *  one obvious thing to do on the screen. */
  primary?: boolean;
};

/* Sprites rather than line icons. A pixel wordmark sitting above a row of
   Lucide strokes was the mismatch that made this screen feel bolted together.
   Statistics gets a drawn glyph because the only candidate sprite, `5bar.png`,
   is a broken export - mostly blank canvas with a red smudge in one corner. */
const MENU: MenuItem[] = [
  { label: "Start Game", to: "/create-game", sprite: sprites.table, primary: true },
  { label: "Create User", to: "/create-user", sprite: sprites.bluePlayerTorso },
  { label: "View User", to: "/view-user", sprite: sprites.redPlayerTorso },
  { label: "Leaderboards", to: "/leaderboards", sprite: sprites.trophy },
  { label: "Statistics", to: "/statistics", glyph: "chart" },
];

const Home = () => {
  const navigate = useNavigate();
  const dispatch: AppDispatch = useDispatch();

  const userStatus = useSelector((state: RootState) => state.users.status);

  useEffect(() => {
    if (userStatus === "idle") {
      dispatch(fetchAllUsers());
    }
  }, [dispatch, userStatus]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-3xl">
        {/* Wordmark flanked by the two teams. */}
        <div className="mb-10 flex items-center justify-center gap-4 sm:gap-8">
          <PixelImg
            src={sprites.bluePlayer}
            outlined
            className="hidden h-44 w-auto sm:block"
          />
          <div className="text-center">
            <h1 className="font-display text-3xl sm:text-5xl">Foosgoos</h1>
            <p className="mt-4 text-sm text-muted-foreground">
              Camera-assisted foosball scorekeeping.
            </p>
          </div>
          <PixelImg
            src={sprites.redPlayer}
            outlined
            className="hidden h-44 w-auto sm:block"
          />
        </div>

        <Card className="p-4 sm:p-6">
          <nav className="grid gap-4 sm:grid-cols-2">
            {MENU.map(({ label, to, sprite, glyph, primary }) => (
              <button
                key={to}
                onClick={() => navigate(to)}
                className={`group flex items-center gap-4 rounded-base border-2 border-border px-4 py-3
                            text-left shadow-shadow transition-all duration-150
                            hover:translate-x-[2px] hover:translate-y-[2px]
                            hover:shadow-[2px_2px_0px_0px_var(--border)]
                            active:translate-x-boxShadowX active:translate-y-boxShadowY active:shadow-none
                            focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring
                            focus-visible:ring-offset-2 focus-visible:ring-offset-background
                            ${
                              primary
                                ? "bg-main sm:col-span-2"
                                : "bg-secondary-background"
                            }`}
              >
                <span className="flex size-14 shrink-0 items-center justify-center rounded-base border-2 border-border bg-secondary-background">
                  {sprite ? (
                    <PixelImg src={sprite} className="max-h-11 w-auto" />
                  ) : (
                    <PixelIcon name={glyph!} className="size-7" />
                  )}
                </span>
                <span className="font-heading text-xl">{label}</span>
              </button>
            ))}
          </nav>
        </Card>
      </div>
    </div>
  );
};

export default Home;
