import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import "../styles/ViewUser.css";
import bluePlayer from "../assets/blue_player.svg"; // Ensure this file exists!

import { useSelector } from "react-redux";
import { type RootState } from "@/store";
import { type User } from "@/types/Game";

type Props = {};

const ViewUser = (_props: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");

  // Accessing the correct slice path
  const allUsers = useSelector((state: RootState) => state.users.users);

  const [selected, setSelected] = useState<User | null>(null);
  const navigate = useNavigate();

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allUsers;
    return allUsers.filter((p) => p.name.toLowerCase().includes(q));
  }, [query, allUsers]);

  function choosePlayer(p: User) {
    setSelected(p);
    setIsOpen(false);
    setQuery("");
    // NOTE: In the future, you should dispatch an action here to fetch
    // specific stats for this user from the backend API (/stats/users?username=...)
  }

  return (
    <div className="view-user-page">
      <div className="return-container">
        <Button variant="neutral" onClick={() => navigate("/")}>
          Return Home
        </Button>
      </div>
      <div className="search-container">
        <button className="search-toggle" onClick={() => setIsOpen((s) => !s)}>
          Search Player ▾
        </button>

        {isOpen && (
          <div className="search-dropdown">
            <input
              className="search-input"
              placeholder="Type a player name..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
            <ul className="search-results">
              {filtered.map((p) => (
                <li
                  key={p.id}
                  className="search-item"
                  onClick={() => choosePlayer(p)}
                >
                  {p.name}
                </li>
              ))}
              {filtered.length === 0 && (
                <li className="search-empty">No players found</li>
              )}
            </ul>
          </div>
        )}
      </div>

      <div className="player-visual">
        <img src={bluePlayer} alt="Blue player" className="blue-player-img" />
      </div>

      <div className="user-info">
        <h2 className="username">
          {selected ? selected.name : "No user selected"}
        </h2>

        {/* The backend currently only tracks goals/saves, NOT wins/losses.
            I have updated this to reflect what our DB actually has.
        */}
        <div className="stats">
          <div className="stat-row">
            <span className="stat-label">Total Goals</span>
            <span className="stat-value">
              {selected && selected.stats ? selected.stats.goals : "0"}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Saves</span>
            <span className="stat-value">
              {selected && selected.stats ? selected.stats.saves : "0"}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Offense Goals</span>
            <span className="stat-value">
              {selected && selected.stats
                ? selected.stats.goals_from_offense
                : "0"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ViewUser;
