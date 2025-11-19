import { useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { type RootState, type AppDispatch } from "@/store";
import { fetchAllUsers } from "@/features/user/userSlice";
import { Button } from "@/components/ui/button";

const LeaderBoards = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  const { users, status } = useSelector((state: RootState) => state.users);

  // Force a data refresh when page loads to ensure stats are up-to-date
  useEffect(() => {
    dispatch(fetchAllUsers());
  }, [dispatch]);

  // Sort users by Total Goals (Highest first)
  const sortedUsers = useMemo(() => {
    return [...users].sort((a, b) => {
      const goalsA = a.stats?.goals || 0;
      const goalsB = b.stats?.goals || 0;
      return goalsB - goalsA; // Descending sort
    });
  }, [users]);

  // Helper for medal colors
  const getRankStyle = (index: number) => {
    if (index === 0) return "bg-yellow-100 border-yellow-400 text-yellow-700"; // Gold
    if (index === 1) return "bg-gray-100 border-gray-400 text-gray-700"; // Silver
    if (index === 2) return "bg-orange-100 border-orange-400 text-orange-700"; // Bronze
    return "bg-white border-gray-100 text-gray-600";
  };

  return (
    <div className="min-h-screen bg-[#FEFADC] p-8 flex flex-col items-center gap-6">
      {/* Header */}
      <div className="w-full max-w-2xl flex justify-between items-center">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-gray-800">Leaderboard</h1>
        </div>
        <Button onClick={() => navigate("/")} variant="neutral">
          Return Home
        </Button>
      </div>

      {/* Content */}
      {status === "loading" ? (
        <p className="mt-10 text-gray-500">Updating scores...</p>
      ) : (
        <div className="w-full max-w-2xl flex flex-col gap-3">
          {/* Table Header */}
          <div className="grid grid-cols-12 gap-4 px-6 py-2 text-sm font-bold text-gray-400 uppercase tracking-wider">
            <div className="col-span-2 text-center">Rank</div>
            <div className="col-span-6">Player</div>
            <div className="col-span-4 text-right">Total Goals</div>
          </div>

          {/* The List */}
          {sortedUsers.map((user, index) => (
            <div
              key={user.id}
              className={`grid grid-cols-12 gap-4 px-6 py-4 rounded-xl border-2 items-center shadow-sm transition-transform hover:scale-[1.01] ${getRankStyle(
                index
              )}`}
            >
              {/* Rank # */}
              <div className="col-span-2 text-center font-black text-xl">
                #{index + 1}
              </div>

              {/* Player Name */}
              <div className="col-span-6 font-bold text-lg truncate">
                {user.name}
              </div>

              {/* Score */}
              <div className="col-span-4 text-right">
                <span className="text-2xl font-black">
                  {user.stats?.goals || 0}
                </span>
                <span className="text-xs ml-1 opacity-70 font-medium">
                  GOALS
                </span>
              </div>
            </div>
          ))}

          {sortedUsers.length === 0 && (
            <div className="text-center py-10 text-gray-500 bg-white rounded-xl border-2 border-gray-100">
              No players found. Go create some users!
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default LeaderBoards;
