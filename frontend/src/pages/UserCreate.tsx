import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/input";
import { PixelImg } from "@/components/ui/PixelImg";
import PageShell from "@/components/layout/PageShell";
import { sprites } from "@/pixel_assets/sprites";
import { type AppDispatch } from "@/store";
import { createNewUser } from "@/features/user/userSlice";


const UserCreate: React.FC = () => {
  const [username, setUsername] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const dispatch: AppDispatch = useDispatch();

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = username.trim();
    if (!name) {
      setError("Enter a username first.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await dispatch(createNewUser({ name })).unwrap();
      navigate("/");
    } catch (err: any) {
      console.error("Error creating user:", err);
      setError(err?.message ?? "Could not create that user.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageShell
      title="Create User"
      subtitle="New players need an account before they can be picked for a game."
      icon={sprites.bluePlayerTorso}
      width="regular"
    >
      <Card className="mx-auto max-w-lg p-6 sm:p-8">
        {/* The torsos used to be pinned to the window corners, where they
            collided with the header on anything narrower than a laptop.
            Inside the card they read as an illustration instead. */}
        <div className="flex items-end justify-center gap-8">
          <PixelImg src={sprites.bluePlayer} outlined className="h-36 w-auto" />
          <PixelImg src={sprites.redPlayer} outlined className="h-36 w-auto" />
        </div>

        <form onSubmit={handleCreateUser} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="username" className="text-sm font-heading">
              Username
            </label>
            <Input
              id="username"
              type="text"
              placeholder="e.g. goosemaster"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                if (error) setError(null);
              }}
              autoFocus
            />
          </div>

          {error && (
            <p className="rounded-base border-2 border-border bg-danger-soft px-3 py-2 text-sm font-heading text-foreground">
              {error}
            </p>
          )}

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button
              type="button"
              variant="neutral"
              className="sm:flex-1"
              onClick={() => navigate("/")}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="sm:flex-1"
              disabled={submitting || !username.trim()}
            >
              {submitting ? "Creating..." : "Create User"}
            </Button>
          </div>
        </form>
      </Card>
    </PageShell>
  );
};

export default UserCreate;
