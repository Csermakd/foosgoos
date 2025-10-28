import React, { useState } from "react";
import { useNavigate } from 'react-router-dom'
import { Button } from "../components/ui/button";
import RedPlayerTorso from "../pixel_assets/characters/red_player_torso.png";
import BluePlayerTorso from "../pixel_assets/characters/blue_player_torso.png";

const UserCreate: React.FC = () => {
  const [username, setUsername] = useState("");
  const navigate = useNavigate()

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-6">
      <img
        src={RedPlayerTorso}
        alt="Red Character"
        className="absolute top-4 left-4 w-32 h-32"
      />
      <img
        src={BluePlayerTorso}
        alt="Blue Character"
        className="absolute top-4 right-4 w-32 h-32"
      />
      <h2 className="text-2xl font-bold">Create New User</h2>
      <input
        type="text"
        placeholder="Enter username"
        value={username}
        onChange={e => setUsername(e.target.value)}
        className="border rounded px-4 py-2 text-lg"
      />
      <div className="flex gap-4">
        <Button variant="neutral" onClick={() => navigate('/')}>Return Home</Button>
        <Button variant="default">Create User</Button>
      </div>
    </div>
  );
};

export default UserCreate;