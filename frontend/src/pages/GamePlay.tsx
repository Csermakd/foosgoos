import React, { useState, useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { type RootState, type AppDispatch } from "@/store";
import { type GoalEvent } from "@/types/Game";
import { createMatch } from "@/features/game/gameSlice";
import { Button } from "@/components/ui/button";
import PlayerCard from "@/components/PlayerCard";

import FooseballTable from "../assets/foosball_table.svg";
import BlueTeamIcon from "../assets/blue_player.svg";
import RedTeamIcon from "../assets/red_player.svg";
import SwitchIcon from "../pixel_assets/buttons/switch_arrow_black.png";

type PlayerGoalStats = {
  "5bar": number;
  "3bar": number;
  goalie: number;
  "2bar": number;
  ownGoal: number;
};

const initialGoalStats: PlayerGoalStats = {
  "5bar": 0,
  "3bar": 0,
  goalie: 0,
  "2bar": 0,
  ownGoal: 0,
};

const GamePlay = () => {
  const initialBlueTeam = useSelector((state: RootState) => state.game.blue);
  const initialRedTeam = useSelector((state: RootState) => state.game.red);

  const dispatch: AppDispatch = useDispatch(); // Added dispatch
  const navigate = useNavigate();

  // Local state for scores
  const [scores, setScores] = useState({ blue: 0, red: 0 });

  // Local state for player goals by bar
  const [playerGoals, setPlayerGoals] = useState<
    Record<string, PlayerGoalStats>
  >({});

  // Event stack for undo/rewind
  const [eventStack, setEventStack] = useState<GoalEvent[]>([]);

  // Local state to manage swappable positions
  const [currentAssignments, setCurrentAssignments] = useState({
    blue: initialBlueTeam,
    red: initialRedTeam,
  });

  const blueDefense = currentAssignments.blue.find(
    (p) => p.position === "defense"
  );
  const blueOffense = currentAssignments.blue.find(
    (p) => p.position === "offense"
  );
  const redDefense = currentAssignments.red.find(
    (p) => p.position === "defense"
  );
  const redOffense = currentAssignments.red.find(
    (p) => p.position === "offense"
  );

  // Debugging logs
  useEffect(() => {
    console.log("Event Stack:", eventStack);
    console.log("Player Goals:", playerGoals);
  }, [eventStack, playerGoals]);

  const handleSwitchSides = (team: "blue" | "red") => {
    setCurrentAssignments((prev) => {
      const teamPlayers = prev[team];
      const newTeamPlayers = teamPlayers.map((player) => {
        if (player.position === "offense")
          return { ...player, position: "defense" };
        if (player.position === "defense")
          return { ...player, position: "offense" };
        return player;
      });
      return { ...prev, [team]: newTeamPlayers };
    });
  };

  const handleGoalRecord = (
    playerName: string,
    position: "offense" | "defense",
    goalType: GoalEvent["goalType"]
  ) => {
    // Check team based on initial assignment (teams don't change, only positions)
    const team = initialBlueTeam.some((p) => p.name === playerName)
      ? "blue"
      : "red";

    const event: GoalEvent = { team, playerName, position, goalType };
    setEventStack((prev) => [...prev, event]);

    // Score logic
    if (goalType === "ownGoal") {
      const opponent = team === "blue" ? "red" : "blue";
      setScores((prev) => ({ ...prev, [opponent]: prev[opponent] + 1 }));
      setPlayerGoals((prev) => ({
        ...prev,
        [playerName]: {
          ...(prev[playerName] || { ...initialGoalStats }),
          ownGoal: (prev[playerName]?.ownGoal || 0) + 1,
        },
      }));
    } else {
      setScores((prev) => ({ ...prev, [team]: prev[team] + 1 }));
      setPlayerGoals((prev) => ({
        ...prev,
        [playerName]: {
          ...(prev[playerName] || { ...initialGoalStats }),
          [goalType]: (prev[playerName]?.[goalType] || 0) + 1,
        },
      }));
    }
  };

  const handleRewind = () => {
    if (eventStack.length === 0) return;
    const lastEvent = eventStack[eventStack.length - 1];
    setEventStack((prev) => prev.slice(0, -1));

    if (lastEvent.goalType === "ownGoal") {
      const opponent = lastEvent.team === "blue" ? "red" : "blue";
      setScores((prev) => ({
        ...prev,
        [opponent]: Math.max(prev[opponent] - 1, 0),
      }));
      setPlayerGoals((prev) => ({
        ...prev,
        [lastEvent.playerName]: {
          ...(prev[lastEvent.playerName] || { ...initialGoalStats }),
          ownGoal: Math.max((prev[lastEvent.playerName]?.ownGoal || 1) - 1, 0),
        },
      }));
    } else {
      setScores((prev) => ({
        ...prev,
        [lastEvent.team]: Math.max(prev[lastEvent.team] - 1, 0),
      }));
      setPlayerGoals((prev) => ({
        ...prev,
        [lastEvent.playerName]: {
          ...(prev[lastEvent.playerName] || { ...initialGoalStats }),
          [lastEvent.goalType]: Math.max(
            (prev[lastEvent.playerName]?.[lastEvent.goalType] || 1) - 1,
            0
          ),
        },
      }));
    }
  };

  const handleFinishMatch = async () => {
    if (!blueDefense || !blueOffense || !redDefense || !redOffense) return;

    const winner: "blue" | "red" | "NONE" =
      scores.blue > scores.red
        ? "blue"
        : scores.red > scores.blue
        ? "red"
        : "NONE";

    // 1. Calculate stats for each player
    const calculatePlayerStats = (playerId: number, playerName: string) => {
      const stats = playerGoals[playerName] || initialGoalStats;
      return {
        user_id: playerId,
        goals:
          (stats["5bar"] || 0) +
          (stats["3bar"] || 0) +
          (stats["goalie"] || 0) +
          (stats["2bar"] || 0),
        goals_from_offense: (stats["5bar"] || 0) + (stats["3bar"] || 0),
        goals_from_defense: (stats["goalie"] || 0) + (stats["2bar"] || 0),
        saves: 0,
      };
    };

    const playerStatsList = [
      calculatePlayerStats(blueOffense.id, blueOffense.name),
      calculatePlayerStats(blueDefense.id, blueDefense.name),
      calculatePlayerStats(redOffense.id, redOffense.name),
      calculatePlayerStats(redDefense.id, redDefense.name),
    ];

    const matchData = {
      player1_id: blueOffense.id,
      player2_id: blueDefense.id,
      player3_id: redOffense.id,
      player4_id: redDefense.id,
      winner_team: winner,
      score_blue: scores.blue,
      score_red: scores.red,
      player_stats: playerStatsList,
    };

    try {
      await dispatch(createMatch(matchData)).unwrap();
      alert(`Match Saved! Winner: ${winner.toUpperCase()}`);
      navigate("/");
    } catch (error: any) {
      console.error("Error submitting match:", error);
      alert(`Error saving match: ${error.message}`);
    }
  };

  if (!blueDefense || !blueOffense || !redDefense || !redOffense) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-red-500 font-bold">
          Error loading players. Did you start the game correctly?
        </p>
        <Button onClick={() => navigate("/")}>Go Back</Button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen w-screen gap-8 bg-gray-700 p-8">
      {/* Blue Team */}
      <div className="flex flex-col items-center gap-8 flex-1">
        <h2 className="text-4xl font-black text-blue-400 drop-shadow-md">
          {scores.blue}
        </h2>
        <PlayerCard
          player={blueDefense}
          teamIcon={BlueTeamIcon}
          stats={playerGoals[blueDefense.name] || initialGoalStats}
          onGoal={handleGoalRecord}
        />
        <Button
          variant="neutral"
          size="icon"
          onClick={() => handleSwitchSides("blue")}
        >
          <img src={SwitchIcon} alt="Switch Blue Team" className="w-6 h-6" />
        </Button>
        <PlayerCard
          player={blueOffense}
          teamIcon={BlueTeamIcon}
          stats={playerGoals[blueOffense.name] || initialGoalStats}
          onGoal={handleGoalRecord}
        />
      </div>

      {/* Center Column */}
      <div className="flex flex-col items-center justify-center flex-2">
        <img
          src={FooseballTable}
          alt="Foosball Table"
          className="w-full max-w-xl h-auto drop-shadow-2xl"
        />
        <div className="flex gap-4 mt-8 w-full max-w-xl">
          <Button
            onClick={handleRewind}
            disabled={eventStack.length === 0}
            className="flex-1"
            variant="neutral"
          >
            Rewind
          </Button>
          <Button
            onClick={handleFinishMatch}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white border-none"
          >
            Finish Match
          </Button>
        </div>
      </div>

      {/* Red Team */}
      <div className="flex flex-col items-center gap-8 flex-1">
        <h2 className="text-4xl font-black text-red-400 drop-shadow-md">
          {scores.red}
        </h2>
        <PlayerCard
          player={redOffense}
          teamIcon={RedTeamIcon}
          stats={playerGoals[redOffense.name] || initialGoalStats}
          onGoal={handleGoalRecord}
        />
        <Button
          variant="neutral"
          size="icon"
          onClick={() => handleSwitchSides("red")}
        >
          <img src={SwitchIcon} alt="Switch Red Team" className="w-6 h-6" />
        </Button>
        <PlayerCard
          player={redDefense}
          teamIcon={RedTeamIcon}
          stats={playerGoals[redDefense.name] || initialGoalStats}
          onGoal={handleGoalRecord}
        />
      </div>
    </div>
  );
};

export default GamePlay;
