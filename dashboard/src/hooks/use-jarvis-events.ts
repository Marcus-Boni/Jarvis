"use client";

import { useEffect, useState } from "react";

export type RuntimeEvent = {
  payload: Record<string, unknown>;
  timestamp: string;
  type: string;
};

export function useJarvisEvents() {
  const [events, setEvents] = useState<RuntimeEvent[]>([]);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8000/ws/events");
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as RuntimeEvent;
      setEvents((currentEvents) => [payload, ...currentEvents].slice(0, 12));
    };
    return () => {
      socket.close();
    };
  }, []);

  return { events };
}

