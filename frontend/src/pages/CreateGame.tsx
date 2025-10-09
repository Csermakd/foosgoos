import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/button';
import PlayerSelect from '@/components/PlayerSelect';
import { setPlayers } from '@/features/game/gameSlice';

type Props = {};

type Position = 'offense' | 'defense';

// TODO: Fetch player options from redux store once implemented
const playerOptions = ['Alice', 'Bob', 'Charlie', 'Diana', 'Ethan', 'Fiona'];

const CreateGame = (props: Props) => {
  const [bluePlayer1Name, setBluePlayer1Name] = useState<string>('');
  const [bluePlayer2Name, setBluePlayer2Name] = useState<string>('');
  const [redPlayer1Name,  setRedPlayer1Name]  = useState<string>('');
  const [redPlayer2Name,  setRedPlayer2Name]  = useState<string>('');

  const [bluePlayer1Position, setBluePlayer1Position] = useState<Position>('offense');
  const [bluePlayer2Position, setBluePlayer2Position] = useState<Position>('defense');
  const [redPlayer1Position,  setRedPlayer1Position]  = useState<Position>('offense');
  const [redPlayer2Position,  setRedPlayer2Position]  = useState<Position>('defense');

  const navigate = useNavigate();
  const dispatch = useDispatch();

  // Duplicate prevention: gather all selected players 
  const selectedPlayers = [bluePlayer1Name, bluePlayer2Name, redPlayer1Name, redPlayer2Name].filter(Boolean);

  const getAvailablePlayers = (currentSelection: string) =>
    playerOptions.filter(
      (p) => !selectedPlayers.includes(p) || p === currentSelection
    );

  // Validity: all four chosen + each team has exactly one offense & one defense
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

    dispatch(
      setPlayers({
        blue: [
            {name: bluePlayer1Name, position: bluePlayer1Position},
            {name: bluePlayer2Name, position: bluePlayer2Position}
        ],
        red: [
            {name: redPlayer1Name, position: redPlayer1Position},
            {name: redPlayer2Name, position: redPlayer2Position}
        ],
      })
    );

    navigate('/game-play');
  };

  return (
    <Card className="p-4 space-y-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <PlayerSelect
          label="Team Blue — Player 1"
          players={getAvailablePlayers(bluePlayer1Name)}
          value={bluePlayer1Name}
          onChange={setBluePlayer1Name}
          position={bluePlayer1Position}
          onPositionChange={setBluePlayer1Position}
        />
        <PlayerSelect
          label="Team Blue — Player 2"
          players={getAvailablePlayers(bluePlayer2Name)}
          value={bluePlayer2Name}
          onChange={setBluePlayer2Name}
          position={bluePlayer2Position}
          onPositionChange={setBluePlayer2Position}
        />
        <PlayerSelect
          label="Team Red — Player 1"
          players={getAvailablePlayers(redPlayer1Name)}
          value={redPlayer1Name}
          onChange={setRedPlayer1Name}
          position={redPlayer1Position}
          onPositionChange={setRedPlayer1Position}
        />
        <PlayerSelect
          label="Team Red — Player 2"
          players={getAvailablePlayers(redPlayer2Name)}
          value={redPlayer2Name}
          onChange={setRedPlayer2Name}
          position={redPlayer2Position}
          onPositionChange={setRedPlayer2Position}
        />

        {!isFormValid && (
          <p className="text-sm text-muted-foreground">
            Pick all four players. Each team must have one offense and one defense.
          </p>
        )}

        <Button type="submit" disabled={!isFormValid}>
          Start Game
        </Button>
      </form>
    </Card>
  );
};

export default CreateGame;

