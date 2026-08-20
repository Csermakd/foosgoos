import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { Button } from "@/components/ui/button";
import PlayerSelect from "@/components/PlayerSelect";
import {
  startMatch,
  resumeActiveMatch,
  abandonMatch,
  fetchActiveMatch,
} from "@/features/game/gameSlice";
// UPDATED: Removed space from filename import
import FooseballTable from "../assets/foosball_table.svg";
import BlueTeamIcon from "../assets/blue_player.svg";
import RedTeamIcon from "../assets/red_player.svg";
import { type RootState, type AppDispatch } from "@/store";

const CreateGame = () => {
  // Updated selector to match userSlice structure
  const { users: allUsers, status } = useSelector(
    (state: RootState) => state.users
  );

  const [bluePlayer1Name, setBluePlayer1Name] = useState<string>("");
  const [bluePlayer2Name, setBluePlayer2Name] = useState<string>("");
  const [redPlayer1Name, setRedPlayer1Name] = useState<string>("");
  const [redPlayer2Name, setRedPlayer2Name] = useState<string>("");

  const navigate = useNavigate();
  const dispatch: AppDispatch = useDispatch();
  const [submitting, setSubmitting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  // Set when a previous game was never finished - a closed tab, a crash,
  // someone wandering off. Without a way out of this, every future
  // "Start Game" would fail with a 409 and no obvious remedy.
  const [strandedMatch, setStrandedMatch] = useState<number | null>(null);

  const playerOptions = allUsers.map((user) => user.name);

  const selectedPlayers = [
    bluePlayer1Name,
    bluePlayer2Name,
    redPlayer1Name,
    redPlayer2Name,
  ].filter(Boolean);

  const getAvailablePlayers = (currentSelection: string) =>
    playerOptions.filter(
      (p) => !selectedPlayers.includes(p) || p === currentSelection
    );

  const allChosen =
    bluePlayer1Name && bluePlayer2Name && redPlayer1Name && redPlayer2Name;

  const isFormValid = Boolean(allChosen);

  /**
   * Starting a game now creates the match on the SERVER first, before
   * anyone plays a point. That is what gives the camera something to
   * attach goals and a video recording to - the vision service polls
   * /matches/active and starts working the moment this succeeds.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid || submitting) return;
    setSubmitting(true);
    setStartError(null);

    const getUserByName = (name: string) => {
      const user = allUsers.find((u) => u.name === name);
      // Safety check
      if (!user) throw new Error(`Could not find user ${name}`);
      return user;
    };

    try {
      await dispatch(
        startMatch({
          blue: [
            {
              name: bluePlayer1Name,
              position: "defense",
              id: getUserByName(bluePlayer1Name).id,
            },
            {
              name: bluePlayer2Name,
              position: "offense",
              id: getUserByName(bluePlayer2Name).id,
            },
          ],
          red: [
            {
              name: redPlayer1Name,
              position: "offense",
              id: getUserByName(redPlayer1Name).id,
            },
            {
              name: redPlayer2Name,
              position: "defense",
              id: getUserByName(redPlayer2Name).id,
            },
          ],
        })
      ).unwrap();
      navigate("/game-play");
    } catch (err: any) {
      console.error(err);
      setStartError(
        err?.message ?? "Could not start the game. Is the backend running?"
      );
      // The most likely cause by far is a game somebody never finished.
      // Ask the server directly rather than parsing the error text - the
      // wording of a message is not an API.
      try {
        const active = await dispatch(fetchActiveMatch()).unwrap();
        setStrandedMatch(active ? active.id : null);
      } catch {
        setStrandedMatch(null);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleResume = async () => {
    try {
      await dispatch(resumeActiveMatch(allUsers)).unwrap();
      navigate("/game-play");
    } catch (err: any) {
      setStartError(err?.message ?? "Could not resume that game");
      setStrandedMatch(null);
    }
  };

  const handleAbandon = async () => {
    if (strandedMatch === null) return;
    try {
      await dispatch(abandonMatch(strandedMatch)).unwrap();
      setStartError(null);
      setStrandedMatch(null);
    } catch (err: any) {
      setStartError(err?.message ?? "Could not abandon that game");
    }
  };

  if (status === "loading") {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#FEFADC]">
        Loading players...
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen w-screen gap-8 bg-[#FEFADC]">
      {/* Blue Team Selection */}
      <div className="flex flex-col items-center gap-8 flex-1">
        <div className="flex flex-col items-center gap-4 w-full">
          <div className="flex flex-col items-center gap-2 w-full">
            <img
              src={BlueTeamIcon}
              alt="Blue Defense"
              className="w-8 h-8 mx-auto"
            />
            <PlayerSelect
              label="Blue Defense"
              players={getAvailablePlayers(bluePlayer1Name)}
              value={bluePlayer1Name}
              onChange={setBluePlayer1Name}
            />
          </div>
          <div className="flex flex-col items-center gap-2 w-full">
            <img
              src={BlueTeamIcon}
              alt="Blue Offense"
              className="w-8 h-8 mx-auto"
            />
            <PlayerSelect
              label="Blue Offense"
              players={getAvailablePlayers(bluePlayer2Name)}
              value={bluePlayer2Name}
              onChange={setBluePlayer2Name}
            />
          </div>
        </div>
      </div>

      {/* Center Table */}
      <div className="flex flex-col items-center justify-center flex-2 bg-[#FEFADC] rounded-xl shadow-md p-8">
        <img
          src={FooseballTable}
          alt="Foosball Table"
          className="w-full max-w-xl h-auto"
        />
        <form onSubmit={handleSubmit} className="mt-8 w-full">
          {!isFormValid && (
            <p className="text-sm text-muted-foreground mb-4 text-center">
              Pick all four players.
            </p>
          )}
          {startError && (
            <div className="mb-4 rounded-md border-2 border-red-300 bg-red-50 p-3">
              <p className="text-sm text-red-700 font-bold text-center">
                {startError}
              </p>
              {strandedMatch !== null && (
                <>
                  <p className="text-xs text-red-700/80 text-center mt-1">
                    Somebody left a game open. Pick it back up, or throw it
                    away and start fresh.
                  </p>
                  <div className="flex gap-2 mt-3">
                    <Button
                      type="button"
                      variant="neutral"
                      className="flex-1"
                      onClick={handleResume}
                    >
                      Resume that game
                    </Button>
                    <Button
                      type="button"
                      variant="neutral"
                      className="flex-1 text-red-600"
                      onClick={handleAbandon}
                    >
                      Abandon it
                    </Button>
                  </div>
                </>
              )}
            </div>
          )}
          <Button
            type="submit"
            disabled={!isFormValid || submitting}
            className="w-full"
          >
            {submitting ? "Starting..." : "Start Game"}
          </Button>
        </form>
      </div>

      {/* Red Team Selection */}
      <div className="flex flex-col items-center gap-8 flex-1">
        <div className="flex flex-col items-center gap-4 w-full">
          <div className="flex flex-col items-center gap-2 w-full">
            <img
              src={RedTeamIcon}
              alt="Red Offense"
              className="w-8 h-8 mx-auto"
            />
            <PlayerSelect
              label="Red Offense"
              players={getAvailablePlayers(redPlayer1Name)}
              value={redPlayer1Name}
              onChange={setRedPlayer1Name}
            />
          </div>
          <div className="flex flex-col items-center gap-2 w-full">
            <img
              src={RedTeamIcon}
              alt="Red Defense"
              className="w-8 h-8 mx-auto"
            />
            <PlayerSelect
              label="Red Defense"
              players={getAvailablePlayers(redPlayer2Name)}
              value={redPlayer2Name}
              onChange={setRedPlayer2Name}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
export default CreateGame;
