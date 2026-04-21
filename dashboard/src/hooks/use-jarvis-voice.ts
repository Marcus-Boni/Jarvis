"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type VoiceState = "idle" | "listening" | "processing" | "speaking";
type VoiceConnectionStatus = "connecting" | "connected" | "disconnected";

type UseJarvisVoiceArgs = {
  onAssistantChunk: (chunk: string) => void;
  onAssistantDone: () => void;
  onTranscript: (transcript: string) => void;
};

export function useJarvisVoice({
  onAssistantChunk,
  onAssistantDone,
  onTranscript,
}: UseJarvisVoiceArgs) {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [connectionStatus, setConnectionStatus] = useState<VoiceConnectionStatus>("connecting");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectDelayRef = useRef(500);
  const reconnectTimerRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus("connecting");
    const socket = new WebSocket("ws://localhost:8000/ws/voice");
    socketRef.current = socket;

    socket.onopen = () => {
      reconnectDelayRef.current = 500;
      setConnectionStatus("connected");
    };

    socket.onmessage = async (event) => {
      const payload = JSON.parse(event.data) as {
        type: string;
        text?: string;
        audio_base64?: string;
      };
      if (payload.type === "transcript" && payload.text) {
        onTranscript(payload.text);
        setVoiceState("processing");
      }
      if (payload.type === "chunk" && payload.text) {
        onAssistantChunk(payload.text);
      }
      if (payload.type === "audio" && payload.audio_base64) {
        setVoiceState("speaking");
        await playBase64Audio(payload.audio_base64);
      }
      if (payload.type === "done") {
        onAssistantDone();
        setVoiceState("idle");
      }
    };

    socket.onclose = () => {
      setConnectionStatus("disconnected");
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      reconnectTimerRef.current = window.setTimeout(() => {
        connect();
      }, reconnectDelayRef.current);
      reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 8000);
    };
  }, [onAssistantChunk, onAssistantDone, onTranscript]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      socketRef.current?.close();
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, [connect]);

  const startListening = useCallback(async () => {
    const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = mediaStream;
    chunksRef.current = [];
    const mediaRecorder = new MediaRecorder(mediaStream);
    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.ondataavailable = (event) => {
      chunksRef.current.push(event.data);
    };
    mediaRecorder.onstop = async () => {
      if (socketRef.current?.readyState !== WebSocket.OPEN) {
        setVoiceState("idle");
        return;
      }

      setVoiceState("processing");
      const blob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType || "audio/webm" });
      socketRef.current.send(
        JSON.stringify({
          type: "start",
          session_id: "dashboard-voice",
          locale: "pt-BR",
        })
      );
      socketRef.current.send(await blob.arrayBuffer());
      socketRef.current.send(JSON.stringify({ type: "end" }));
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    };
    mediaRecorder.start();
    setVoiceState("listening");
  }, []);

  const stopListening = useCallback(() => {
    mediaRecorderRef.current?.stop();
  }, []);

  const toggleListening = useCallback(async () => {
    if (voiceState === "listening") {
      stopListening();
      return;
    }
    if (voiceState === "idle") {
      await startListening();
    }
  }, [startListening, stopListening, voiceState]);

  return {
    toggleListening,
    voiceConnectionStatus: connectionStatus,
    voiceState,
  };
}

async function playBase64Audio(audioBase64: string) {
  const binary = Uint8Array.from(atob(audioBase64), (char) => char.charCodeAt(0));
  const audioContext = new AudioContext();
  const audioBuffer = await audioContext.decodeAudioData(binary.buffer.slice(0));
  const source = audioContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioContext.destination);
  source.start();
}

