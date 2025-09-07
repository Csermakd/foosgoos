import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/button';
import PlayerSelect from '@/components/PlayerSelect';
import { setPlayers } from '@/features/game/gameSlice';

type Props = {};

//TODO: Fetch player options from redux store once implemented
const playerOptions = [
  'Alice',
  'Bob',
  'Charlie',
  'Diana',
  'Ethan',
  'Fiona',
];

const CreateGame = (props: Props) => {
  const [teamABluePlayer1, setTeamABluePlayer1] = useState<string>('');
  const [teamABluePlayer2, setTeamABluePlayer2] = useState<string>('');
  const [teamBRedPlayer1, setTeamBRedPlayer1] = useState<string>('');
  const [teamBRedPlayer2, setTeamBRedPlayer2] = useState<string>('');

  const navigate = useNavigate();
  const dispatch = useDispatch();

  // Player selection and filtering logic
  const selectedPlayers = [teamABluePlayer1, teamABluePlayer2, teamBRedPlayer1, teamBRedPlayer2].filter(Boolean);
  const getAvailablePlayers = (currentSelection: string) => {
      return playerOptions.filter(player => !selectedPlayers.includes(player) || player === currentSelection);
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle navigation or state update here
    // dispatch players to redux store
    dispatch(setPlayers({
      blue: [teamABluePlayer1, teamABluePlayer2],
      red: [teamBRedPlayer1, teamBRedPlayer2],
    }));
    navigate('/game-play');

    console.log('Team A:', teamABluePlayer1, teamABluePlayer2);
    console.log('Team B:', teamBRedPlayer1, teamBRedPlayer2);
  };

  return (
    <Card>
      <form onSubmit={handleSubmit}>
        <PlayerSelect
          label="Team Blue - Player 1"
          players={getAvailablePlayers(teamABluePlayer1)}
          value={teamABluePlayer1}
          onChange={setTeamABluePlayer1}
        />
        <PlayerSelect
          label="Team Blue - Player 2"
          players={getAvailablePlayers(teamABluePlayer2)}
          value={teamABluePlayer2}
          onChange={setTeamABluePlayer2}
        />
        <PlayerSelect
          label="Team Red - Player 1"
          players={getAvailablePlayers(teamBRedPlayer1)}
          value={teamBRedPlayer1}
          onChange={setTeamBRedPlayer1}
        />
        <PlayerSelect
          label="Team Red - Player 2"
          players={getAvailablePlayers(teamBRedPlayer2)}
          value={teamBRedPlayer2}
          onChange={setTeamBRedPlayer2}
        />
        <Button type="submit">Start Game</Button>
      </form>
    </Card>
  );
};

export default CreateGame;

