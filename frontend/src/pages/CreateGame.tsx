import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Button } from '@/components/ui/button';
import PlayerSelect from '@/components/PlayerSelect';
import { setPlayers } from '@/features/game/gameSlice';
import FooseballTable from '../assets/Foosball Table.svg';
import BlueTeamIcon from '../assets/blue_player.svg';
import RedTeamIcon from '../assets/red_player.svg';

interface User {
  id: number;
  name: string;
}

type Props = {};

// type Position = 'offense' | 'defense';

// TODO: Fetch player options from redux store once implemented
// const playerOptions = ['Alice', 'Bob', 'Charlie', 'Diana', 'Ethan', 'Fiona'];

const CreateGame = (props: Props) => {
  const [allUsers, setAllUsers] = useState<User[]>([]);
  
  const [bluePlayer1Name, setBluePlayer1Name] = useState<string>('');
  const [bluePlayer2Name, setBluePlayer2Name] = useState<string>('');
  const [redPlayer1Name, setRedPlayer1Name] = useState<string>('');
  const [redPlayer2Name, setRedPlayer2Name] = useState<string>('');

  const [bluePlayer1Position, setBluePlayer1Position] = useState<Position>('offense');
  const [bluePlayer2Position, setBluePlayer2Position] = useState<Position>('defense');
  const [redPlayer1Position, setRedPlayer1Position] = useState<Position>('offense');
  const [redPlayer2Position, setRedPlayer2Position] = useState<Position>('defense');

  const navigate = useNavigate();
  const dispatch = useDispatch();

  // fetching users from backend when component loads

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await fetch("http://localhost:8000/users/all");
        if (!response.ok) {
          throw new Error("Failed to fetch all users");
        }
        const users: User[] = await response.json();
        setAllUsers(users);
      }
      catch (error) {
        console.error(error);
      }
    };
    fetchUsers();
  }, []);

  // player options are now dynamic, based on fetched user list

  const playerOptions = allUsers.map(user => user.name);

  // Duplicate prevention: gather all selected players 
  const selectedPlayers = [bluePlayer1Name, bluePlayer2Name, redPlayer1Name, redPlayer2Name].filter(Boolean);
  const getAvailablePlayers = (currentSelection: string) =>
    playerOptions.filter(
      (p) => !selectedPlayers.includes(p) || p === currentSelection
    );
  // Validity: all four chosen
  const allChosen =
    bluePlayer1Name && bluePlayer2Name && redPlayer1Name && redPlayer2Name;
  
  const bluePositionsValid =
    [bluePlayer1Position, bluePlayer2Position].sort().join('-') ===
    ['defense', 'offense'].sort().join('-');

  const redPositionsValid =
    [redPlayer1Position, redPlayer2Position].sort().join('-') ===
    ['defense', 'offense'].sort().join('-');

  const isFormValid = Boolean(allChosen && bluePositionsValid && redPositionsValid);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) return;

    // helper to find full user object with ID by name
    const getUserByName = (name: string) => {
      const user = allUsers.find(u => u.name === name);
      if (!user) throw new Error('Could not find user ${name}');
      return user;
    };

    dispatch(
      setPlayers({
        blue: [
            {name: bluePlayer1Name, position: bluePlayer1Position, id: getUserByName(bluePlayer1Name).id },
            {name: bluePlayer2Name, position: bluePlayer2Position, id: getUserByName(bluePlayer2Name).id }
        ],
        red: [
            {name: redPlayer1Name, position: redPlayer1Position, id: getUserByName(redPlayer1Name).id },
            {name: redPlayer2Name, position: redPlayer2Position, id: getUserByName(redPlayer2Name).id }
        ],
      })
    );
    navigate('/game-play');
  };
  return (
    <div className="flex items-center justify-center min-h-screen w-screen gap-8 bg-[#FEFADC]">
      {/* Blue Team Selection */}
      <div className="flex flex-col items-center gap-8 flex-1">
        <div className="flex flex-col items-center gap-4 w-full">
          <div className="flex flex-col items-center gap-2 w-full">
            <img src={BlueTeamIcon} alt="Blue Defense" className="w-8 h-8 mx-auto" />
            <PlayerSelect
              label="Blue Defense"
              players={getAvailablePlayers(bluePlayer1Name)}
              value={bluePlayer1Name}
              onChange={setBluePlayer1Name}
            />
          </div>
          <div className="flex flex-col items-center gap-2 w-full">
            <img src={BlueTeamIcon} alt="Blue Offense" className="w-8 h-8 mx-auto" />
            <PlayerSelect
              label="Blue Offense"
              players={getAvailablePlayers(bluePlayer2Name)}
              value={bluePlayer2Name}
              onChange={setBluePlayer2Name}
            />
          </div>
        </div>
      </div>
      {/* Foosball Table SVG */}
      <div className="flex flex-col items-center justify-center flex-2 bg-[#FEFADC] rounded-xl shadow-md p-8">
        <img src={FooseballTable} alt="Foosball Table" className="w-full max-w-xl h-auto" />
        <form onSubmit={handleSubmit} className="mt-8 w-full">
          {!isFormValid && (
            <p className="text-sm text-muted-foreground mb-4">
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
            <img src={RedTeamIcon} alt="Red Offense" className="w-8 h-8 mx-auto" />
            <PlayerSelect
              label="Red Offense"
              players={getAvailablePlayers(redPlayer1Name)}
              value={redPlayer1Name}
              onChange={setRedPlayer1Name}
            />
          </div>
          <div className="flex flex-col items-center gap-2 w-full">
            <img src={RedTeamIcon} alt="Red Defense" className="w-8 h-8 mx-auto" />
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

