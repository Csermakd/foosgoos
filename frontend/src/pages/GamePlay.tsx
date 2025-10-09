import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { type RootState } from '@/store';
import { type PlayerAssignment, type GoalEvent } from '@/types/Game';
import GoalModal from '@/components/GoalModal';

const GOAL_OPTIONS = {
  offense: [
    { label: '5 Bar Goal', value: '5bar' },
    { label: '3 Bar Goal', value: '3bar' },
    { label: 'Own Goal', value: 'ownGoal' },
  ],
  defense: [
    { label: 'Goalie', value: 'goalie' },
    { label: '2 Bar Goal', value: '2bar' },
    { label: 'Own Goal', value: 'ownGoal' },
  ],
};

type PlayerGoalStats = {
  '5bar': number;
  '3bar': number;
  'goalie': number;
  '2bar': number;
  'ownGoal': number;
};

const initialGoalStats: PlayerGoalStats = {
  '5bar': 0,
  '3bar': 0,
  'goalie': 0,
  '2bar': 0,
  'ownGoal': 0,
};

const GamePlay = () => {
  const blueTeam: PlayerAssignment[] = useSelector((state: RootState) => state.game.blue);
  const redTeam: PlayerAssignment[] = useSelector((state: RootState) => state.game.red);

  // Local state for scores
  const [scores, setScores] = useState({ blue: 0, red: 0 });

  // Local state for player goals by bar
  const [playerGoals, setPlayerGoals] = useState<Record<string, PlayerGoalStats>>({});

  // Event stack for undo/rewind
  const [eventStack, setEventStack] = useState<GoalEvent[]>([]);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalPlayer, setModalPlayer] = useState<{
    team: 'blue' | 'red';
    playerName: string;
    position: 'offense' | 'defense';
  } | null>(null);

  // Console log event stack and player totals on change
  useEffect(() => {
    console.log('Event Stack:', eventStack);
    console.log('Player Goals:', playerGoals);
  }, [eventStack, playerGoals]);

  // Open modal when player is clicked
  const handlePlayerClick = (
    team: 'blue' | 'red',
    playerName: string,
    position: 'offense' | 'defense'
  ) => {
    setModalPlayer({ team, playerName, position });
    setModalOpen(true);
  };

  // Handle goal selection from modal
  const handleGoalSelect = (goalType: GoalEvent['goalType']) => {
    if (!modalPlayer) return;
    const { team, playerName, position } = modalPlayer;
    const event: GoalEvent = {
      team,
      playerName,
      position,
      goalType,
    };
    setEventStack(prev => [...prev, event]);

    // Score logic
    if (goalType === 'ownGoal') {
      const opponent = team === 'blue' ? 'red' : 'blue';
      setScores(prev => ({
        ...prev,
        [opponent]: prev[opponent] + 1,
      }));
      setPlayerGoals(prev => ({
        ...prev,
        [playerName]: {
          ...(prev[playerName] || { ...initialGoalStats }),
          ownGoal: (prev[playerName]?.ownGoal || 0) + 1,
        },
      }));
    } else {
      setScores(prev => ({
        ...prev,
        [team]: prev[team] + 1,
      }));
      setPlayerGoals(prev => ({
        ...prev,
        [playerName]: {
          ...(prev[playerName] || { ...initialGoalStats }),
          [goalType]: (prev[playerName]?.[goalType] || 0) + 1,
        },
      }));
    }

    setModalOpen(false);
    setModalPlayer(null);
  };

  // Rewind/undo last event
  const handleRewind = () => {
    if (eventStack.length === 0) return;
    const lastEvent = eventStack[eventStack.length - 1];
    setEventStack(prev => prev.slice(0, -1));
    if (lastEvent.goalType === 'ownGoal') {
      const opponent = lastEvent.team === 'blue' ? 'red' : 'blue';
      setScores(prev => ({
        ...prev,
        [opponent]: Math.max(prev[opponent] - 1, 0),
      }));
      setPlayerGoals(prev => ({
        ...prev,
        [lastEvent.playerName]: {
          ...(prev[lastEvent.playerName] || { ...initialGoalStats }),
          ownGoal: Math.max((prev[lastEvent.playerName]?.ownGoal || 1) - 1, 0),
        },
      }));
    } else {
      setScores(prev => ({
        ...prev,
        [lastEvent.team]: Math.max(prev[lastEvent.team] - 1, 0),
      }));
      setPlayerGoals(prev => ({
        ...prev,
        [lastEvent.playerName]: {
          ...(prev[lastEvent.playerName] || { ...initialGoalStats }),
          [lastEvent.goalType]: Math.max((prev[lastEvent.playerName]?.[lastEvent.goalType] || 1) - 1, 0),
        },
      }));
    }
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
                  {player.name} ({player.position}) - 
                  5bar: {playerGoals[player.name]?.['5bar'] || 0}, 
                  3bar: {playerGoals[player.name]?.['3bar'] || 0}, 
                  goalie: {playerGoals[player.name]?.['goalie'] || 0}, 
                  2bar: {playerGoals[player.name]?.['2bar'] || 0}, 
                  own: {playerGoals[player.name]?.['ownGoal'] || 0}
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
                  {player.name} ({player.position}) - 
                  5bar: {playerGoals[player.name]?.['5bar'] || 0}, 
                  3bar: {playerGoals[player.name]?.['3bar'] || 0}, 
                  goalie: {playerGoals[player.name]?.['goalie'] || 0}, 
                  2bar: {playerGoals[player.name]?.['2bar'] || 0}, 
                  own: {playerGoals[player.name]?.['ownGoal'] || 0}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
      {eventStack.length > 0 && (
        <button onClick={handleRewind}>
          Rewind Last Event
        </button>
      )}
      <GoalModal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setModalPlayer(null); }}
        options={
          modalPlayer
            ? GOAL_OPTIONS[modalPlayer.position]
            : []
        }
        onSelect={handleGoalSelect}
        title={
          modalPlayer
            ? `Record Goal for ${modalPlayer.playerName} (${modalPlayer.position})`
            : ''
        }
      />
    </div>
  );
};

export default GamePlay;

