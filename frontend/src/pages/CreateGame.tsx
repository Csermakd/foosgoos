import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Button } from '@/components/ui/button';
import PlayerSelect from '@/components/PlayerSelect';
import { setPlayers } from '@/features/game/gameSlice';
import FooseballTable from '../assets/Foosball Table.svg';

type Position = 'offense' | 'defense';

// TODO: Fetch player options from redux store once implemented
const playerOptions = ['Alice', 'Bob', 'Charlie', 'Diana', 'Ethan', 'Fiona'];

const CreateGame = () => {
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
          { name: bluePlayer1Name, position: bluePlayer1Position },
          { name: bluePlayer2Name, position: bluePlayer2Position }
        ],
        red: [
          { name: redPlayer1Name, position: redPlayer1Position },
          { name: redPlayer2Name, position: redPlayer2Position }
        ],
      })
    );

    navigate('/game-play');
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#FEFADC',
        minHeight: '100vh',
        width: '100vw',
        gap: '2rem',
      }}
    >
      {/* Blue Team Selection */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '1rem',
      }}>
        <h2 style={{ color: 'blue', fontWeight: 'bold' }}>Blue Team</h2>
        <PlayerSelect
          label="Player 1"
          players={getAvailablePlayers(bluePlayer1Name)}
          value={bluePlayer1Name}
          onChange={setBluePlayer1Name}
          position={bluePlayer1Position}
          onPositionChange={setBluePlayer1Position}
        />
        <PlayerSelect
          label="Player 2"
          players={getAvailablePlayers(bluePlayer2Name)}
          value={bluePlayer2Name}
          onChange={setBluePlayer2Name}
          position={bluePlayer2Position}
          onPositionChange={setBluePlayer2Position}
        />
      </div>

      {/* Foosball Table SVG */}
      <div style={{
        flex: 2,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#FEFADC',
        borderRadius: '1rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
        padding: '2rem',
      }}>
        <img src={FooseballTable} style={{ width: '100%', maxWidth: '500px', height: 'auto' }} />
        <form onSubmit={handleSubmit} style={{ marginTop: '2rem', width: '100%' }}>
          {!isFormValid && (
            <p className="text-sm text-muted-foreground">
              Pick all four players. Each team must have one offense and one defense.
            </p>
          )}
          <Button type="submit" disabled={!isFormValid} style={{ width: '100%' }}>
            Start Game
          </Button>
        </form>
      </div>

      {/* Red Team Selection */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '1rem',
      }}>
        <h2 style={{ color: 'red', fontWeight: 'bold' }}>Red Team</h2>
        <PlayerSelect
          label="Player 1"
          players={getAvailablePlayers(redPlayer1Name)}
          value={redPlayer1Name}
          onChange={setRedPlayer1Name}
          position={redPlayer1Position}
          onPositionChange={setRedPlayer1Position}
        />
        <PlayerSelect
          label="Player 2"
          players={getAvailablePlayers(redPlayer2Name)}
          value={redPlayer2Name}
          onChange={setRedPlayer2Name}
          position={redPlayer2Position}
          onPositionChange={setRedPlayer2Position}
        />
      </div>
    </div>
  );
};

export default CreateGame;

