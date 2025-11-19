import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { Button } from "@/components/ui/button";
import PlayerSelect from "@/components/PlayerSelect";
import { setPlayers } from "@/features/game/gameSlice";
// UPDATED: Removed space from filename import
import FooseballTable from "../assets/foosball_table.svg";
import BlueTeamIcon from "../assets/blue_player.svg";
import RedTeamIcon from "../assets/red_player.svg";
import { type RootState } from "@/store";

type Props = {};

const CreateGame = (props: Props) => {
  // Updated selector to match userSlice structure
  const { users: allUsers, status } = useSelector(
    (state: RootState) => state.users
  );

  const [bluePlayer1Name, setBluePlayer1Name] = useState<string>("");
  const [bluePlayer2Name, setBluePlayer2Name] = useState<string>("");
  const [redPlayer1Name, setRedPlayer1Name] = useState<string>("");
  const [redPlayer2Name, setRedPlayer2Name] = useState<string>("");

  const navigate = useNavigate();
  const dispatch = useDispatch();

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) return;

    const getUserByName = (name: string) => {
      const user = allUsers.find((u) => u.name === name);
      // Safety check
      if (!user) throw new Error(`Could not find user ${name}`);
      return user;
    };

    try {
      dispatch(
        setPlayers({
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
      );
      navigate("/game-play");
    } catch (err) {
      console.error(err);
      alert("Error starting game. Please refresh and try again.");
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
          <Button type="submit" disabled={!isFormValid} className="w-full">
            Start Game
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
