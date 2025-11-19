import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { Button } from "@/components/ui/button";
import { type RootState } from "@/store";

type MatchRecord = {
  id: number;
  timestamp: string;
  winner_team: "blue" | "red" | "NONE";
  score_blue: number;
  score_red: number;
  player1_id: number;
  player2_id: number;
  player3_id: number;
  player4_id: number;
};

const Stats = () => {
  const navigate = useNavigate();
  const [matches, setMatches] = useState<MatchRecord[]>([]);
  const [loading, setLoading] = useState(true);

  // 1. Get the list of users from Redux so we can translate IDs to Names
  const users = useSelector((state: RootState) => state.users.users);

  // Helper to find name by ID
  const getName = (id: number) => {
    const found = users.find((u) => u.id === id);
    return found ? found.name : "Unknown";
  };

  useEffect(() => {
    const fetchMatches = async () => {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_URL}/matches/`);
        if (res.ok) {
          const data = await res.json();
          setMatches(data);
        }
      } catch (error) {
        console.error("Failed to load matches", error);
      } finally {
        setLoading(false);
      }
    };
    fetchMatches();
  }, []);

  return (
    <div className="min-h-screen bg-[#FEFADC] p-8 flex flex-col items-center gap-6">
      <div className="w-full max-w-4xl flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Recent Matches</h1>
        <Button onClick={() => navigate("/")} variant="neutral">
          Return Home
        </Button>
      </div>

      {loading ? (
        <p>Loading match history...</p>
      ) : (
        <div className="w-full max-w-4xl grid gap-4">
          {matches.length === 0 && (
            <div className="text-center text-gray-500 py-10">
              No matches recorded yet.
            </div>
          )}

          {matches.map((match) => (
            <div
              key={match.id}
              className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between border-2 border-gray-100"
            >
              {/* Blue Team Info */}
              <div className="flex-1 text-center">
                <h3 className="font-bold text-blue-600 text-lg">Blue Team</h3>
                <div className="text-4xl font-black text-gray-800 my-2">
                  {match.score_blue}
                </div>
                <div className="flex flex-col gap-1 text-sm text-gray-600">
                  <span>
                    Offense: <b>{getName(match.player1_id)}</b>
                  </span>
                  <span>
                    Defense: <b>{getName(match.player2_id)}</b>
                  </span>
                </div>
              </div>

              {/* VS Badge */}
              <div className="flex flex-col items-center px-6">
                <span className="text-sm font-bold text-gray-400">VS</span>
                <span className="text-xs text-gray-300 mt-1">
                  {new Date(match.timestamp).toLocaleDateString()}
                </span>
                {match.winner_team !== "NONE" && (
                  <span
                    className={`mt-2 px-2 py-1 rounded text-xs font-bold text-white ${
                      match.winner_team === "blue"
                        ? "bg-blue-500"
                        : "bg-red-500"
                    }`}
                  >
                    {match.winner_team.toUpperCase()} WON
                  </span>
                )}
              </div>

              {/* Red Team Info */}
              <div className="flex-1 text-center">
                <h3 className="font-bold text-red-600 text-lg">Red Team</h3>
                <div className="text-4xl font-black text-gray-800 my-2">
                  {match.score_red}
                </div>
                <div className="flex flex-col gap-1 text-sm text-gray-600">
                  <span>
                    Offense: <b>{getName(match.player3_id)}</b>
                  </span>
                  <span>
                    Defense: <b>{getName(match.player4_id)}</b>
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Stats;
