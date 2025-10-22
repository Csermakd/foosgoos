import React, { useState } from "react";
import { Button } from "../components/ui/button";
import RedPlayerTorso from "../pixel_assets/characters/red_player_torso.png";
import BluePlayerTorso from "../pixel_assets/characters/blue_player_torso.png";
import { useNavigate } from "react-router-dom"

const UserCreate: React.FC = () => {
  const [username, setUsername] = useState("");
  const navigate = useNavigate();

  const handleCreateUser = async () => {
    if (!username) {
      alert("Please enter a username.");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/users/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name: username }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create user.");
      }

      const newUser = await response.json();
      console.log("User created:", newUser);
      alert('User "${newUser.name}" created successfully!');
      navigate("/");
    }
    catch (error: any) {
      console.error("Error creating user:", error);
      alert('Error: ${error.message}');
    }
  };

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
        <Button variant="neutral" onClick={() => navigate("/")}>Return Home</Button>
        <Button variant="default" onClick={handleCreateUser}>Create User</Button>
      </div>
    </div>
  );
};

export default UserCreate;