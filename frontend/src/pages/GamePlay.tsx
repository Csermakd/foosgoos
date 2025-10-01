import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { type RootState } from '@/store';
import { type PlayerAssignment, type GoalEvent } from '@/types/Game';

const GamePlay = () => {
  const blueTeam: PlayerAssignment[] = useSelector((state: RootState) => state.game.blue);
  const redTeam: PlayerAssignment[] = useSelector((state: RootState) => state.game.red);

  // Local state for scores
  const [scores, setScores] = useState({ blue: 0, red: 0 });

  // Event stack for undo/rewind
  const [eventStack, setEventStack] = useState<GoalEvent[]>([]);

  // Placeholder for modal trigger
  const handlePlayerClick = (
    team: 'blue' | 'red',
    playerName: string,
    position: 'offense' | 'defense'
  ) => {
    // TODO: Open modal here
    console.log(`Clicked ${playerName} (${position}) from ${team} team`);
    // Example: Simulate a goal event (replace with modal logic)
    const event: GoalEvent = {
      team,
      playerName,
      position,
      goalType: position === 'offense' ? '3bar' : 'goalie',
    };
    setEventStack(prev => [...prev, event]);
    setScores(prev => ({
      ...prev,
      [team]: prev[team] + 1,
    }));
  };

  // Rewind/undo last event
  const handleRewind = () => {
    if (eventStack.length === 0) return;
    const lastEvent = eventStack[eventStack.length - 1];
    setEventStack(prev => prev.slice(0, -1));
    setScores(prev => ({
      ...prev,
      [lastEvent.team]: Math.max(prev[lastEvent.team] - 1, 0),
    }));
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: '2rem' }}>
        <div>
          <h2>Team Blue (Score: {scores.blue})</h2>
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
          <h2>Team Red (Score: {scores.red})</h2>
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
      <button onClick={handleRewind} disabled={eventStack.length === 0}>
        Rewind Last Event
      </button>
    </div>
  );
};

export default GamePlay;

