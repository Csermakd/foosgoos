import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/button';
import PlayerSelect from '@/components/PlayerSelect';

type Props = {};

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle navigation or state update here
    console.log('Team A:', teamABluePlayer1, teamABluePlayer2);
    console.log('Team B:', teamBRedPlayer1, teamBRedPlayer2);
  };

  return (
    <Card>
      <form onSubmit={handleSubmit}>
        <PlayerSelect
          label="Team Blue - Player 1"
          players={playerOptions}
          value={teamABluePlayer1}
          onChange={setTeamABluePlayer1}
        />
        <PlayerSelect
          label="Team Blue - Player 2"
          players={playerOptions}
          value={teamABluePlayer2}
          onChange={setTeamABluePlayer2}
        />
        <PlayerSelect
          label="Team Red - Player 1"
          players={playerOptions}
          value={teamBRedPlayer1}
          onChange={setTeamBRedPlayer1}
        />
        <PlayerSelect
          label="Team Red - Player 2"
          players={playerOptions}
          value={teamBRedPlayer2}
          onChange={setTeamBRedPlayer2}
        />
        <Button type="submit">Start Game</Button>
      </form>
    </Card>
  );
};

export default CreateGame;

