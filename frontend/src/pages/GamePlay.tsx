import { useSelector } from 'react-redux';
import { type RootState } from '@/store';

const GamePlay = () => {
  const blueTeam = useSelector((state: RootState) => state.game.blue);
  const redTeam = useSelector((state: RootState) => state.game.red);

  // Placeholder for modal trigger
  const handlePlayerClick = (team: 'blue' | 'red', playerName: string, position: 'offense' | 'defense') => {
    // TODO: Open modal here
    console.log(`Clicked ${playerName} (${position}) from ${team} team`);
  };

  return (
    <div style={{ display: 'flex', gap: '2rem' }}>
      <div>
        <h2>Team Blue</h2>
        <ul>
          {blueTeam.map((player) => (
            <li key={player.name}>
              <button
                style={{ background: 'none', border: 'none', color: 'blue', cursor: 'pointer' }}
                onClick={() => handlePlayerClick('blue', player.name, player.position)}
              >
                {player.name} ({player.position})
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h2>Team Red</h2>
        <ul>
          {redTeam.map((player) => (
            <li key={player.name}>
              <button
                style={{ background: 'none', border: 'none', color: 'red', cursor: 'pointer' }}
                onClick={() => handlePlayerClick('red', player.name, player.position)}
              >
                {player.name} ({player.position})
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default GamePlay;

