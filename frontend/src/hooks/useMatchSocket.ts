import { useEffect, useRef } from "react";
import { useDispatch } from "react-redux";
import {
  goalReceived,
  goalRemoved,
  setCameraConnected,
  loadMatch,
} from "@/features/game/gameSlice";
import { type AppDispatch } from "@/store";
import { type MatchSocketMessage } from "@/types/Game";

const API_URL = import.meta.env.VITE_API_URL as string;

/** http://host:8000 -> ws://host:8000 (and https -> wss). */
function websocketUrl(matchId: number): string {
  const base = API_URL.replace(/^http/, "ws").replace(/\/$/, "");
  return `${base}/matches/ws/${matchId}`;
}

/**
 * Subscribes to a match's live goal feed.
 *
 * Treats the socket as a hint to update, never as the source of truth:
 * every message carries the score the server derived from the goal log,
 * and on reconnect we re-fetch the whole match rather than trying to
 * replay whatever we missed. That keeps a dropped wifi connection from
 * silently leaving the scoreboard wrong.
 */
export function useMatchSocket(matchId: number | null) {
  const dispatch: AppDispatch = useDispatch();
  const socketRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<number>(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (matchId === null) return;
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      const socket = new WebSocket(websocketUrl(matchId));
      socketRef.current = socket;

      socket.onopen = () => {
        dispatch(setCameraConnected(true));
        // A reconnect may have missed messages, so re-sync from the
        // server instead of assuming our local list is complete.
        if (retryRef.current > 0) dispatch(loadMatch(matchId));
        retryRef.current = 0;
      };

      socket.onmessage = (raw) => {
        const message: MatchSocketMessage = JSON.parse(raw.data);
        switch (message.type) {
          case "goal_added":
          case "goal_updated":
            dispatch(
              goalReceived({ event: message.event, score: message.score })
            );
            break;
          case "goal_deleted":
            dispatch(
              goalRemoved({
                eventId: message.event_id,
                score: message.score,
              })
            );
            break;
          case "match_finished":
            socket.close();
            break;
        }
      };

      socket.onclose = () => {
        dispatch(setCameraConnected(false));
        if (cancelled) return;
        // Back off, but never further than a few seconds - somebody is
        // standing at the table waiting for the score to move.
        const delay = Math.min(1000 * 2 ** retryRef.current, 5000);
        retryRef.current += 1;
        timerRef.current = setTimeout(connect, delay);
      };

      socket.onerror = () => socket.close();
    };

    connect();

    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [matchId, dispatch]);
}
