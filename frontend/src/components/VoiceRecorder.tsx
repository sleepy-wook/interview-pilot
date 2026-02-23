"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { createVoiceSocket } from "@/lib/api";

interface Props {
  onTranscript: (text: string, isFinal: boolean) => void;
  onDone: (transcript: string, voiceMetrics: Record<string, unknown>) => void;
  onError: (msg: string) => void;
  vocabularyName?: string;
  disabled?: boolean;
}

export default function VoiceRecorder({
  onTranscript,
  onDone,
  onError,
  vocabularyName,
  disabled,
}: Props) {
  const [recording, setRecording] = useState(false);
  const [partialText, setPartialText] = useState("");

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const contextRef = useRef<AudioContext | null>(null);

  const cleanup = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (contextRef.current && contextRef.current.state !== "closed") {
      contextRef.current.close();
      contextRef.current = null;
    }
    if (mediaRef.current) {
      mediaRef.current.getTracks().forEach((t) => t.stop());
      mediaRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [cleanup]);

  const startRecording = useCallback(async () => {
    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true },
      });
      mediaRef.current = stream;

      // Create WebSocket (vocabulary is optional, skip if not provided)
      const ws = createVoiceSocket();
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "partial") {
          setPartialText(msg.text);
          onTranscript(msg.text, false);
        } else if (msg.type === "final") {
          setPartialText("");
          onTranscript(msg.text, true);
        } else if (msg.type === "done") {
          setRecording(false);
          cleanup();
          onDone(msg.transcript, msg.voice_metrics);
        } else if (msg.type === "error") {
          setRecording(false);
          cleanup();
          onError(msg.message);
        }
      };

      ws.onerror = () => {
        setRecording(false);
        cleanup();
        onError("WebSocket connection failed");
      };

      ws.onopen = () => {
        // Set up audio processing
        const audioCtx = new AudioContext({ sampleRate: 16000 });
        contextRef.current = audioCtx;
        const source = audioCtx.createMediaStreamSource(stream);

        // Use ScriptProcessorNode to capture raw PCM
        const processor = audioCtx.createScriptProcessor(4096, 1, 1);
        processorRef.current = processor;

        processor.onaudioprocess = (e) => {
          if (ws.readyState !== WebSocket.OPEN) return;
          const float32 = e.inputBuffer.getChannelData(0);
          // Convert float32 to int16 PCM
          const int16 = new Int16Array(float32.length);
          for (let i = 0; i < float32.length; i++) {
            const s = Math.max(-1, Math.min(1, float32[i]));
            int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
          }
          // Base64 encode and send
          const bytes = new Uint8Array(int16.buffer);
          const binary = Array.from(bytes)
            .map((b) => String.fromCharCode(b))
            .join("");
          const b64 = btoa(binary);
          ws.send(JSON.stringify({ type: "audio", data: b64 }));
        };

        source.connect(processor);
        processor.connect(audioCtx.destination);

        setRecording(true);
      };
    } catch (err) {
      onError(
        err instanceof Error ? err.message : "Failed to access microphone"
      );
    }
  }, [vocabularyName, onTranscript, onDone, onError, cleanup]);

  const stopRecording = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "stop" }));
    }
    // Cleanup will happen in the "done" message handler
  }, []);

  return (
    <div className="flex items-center gap-3">
      {recording ? (
        <>
          <button
            onClick={stopRecording}
            className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            <span className="w-3 h-3 bg-white rounded-full recording-pulse" />
            Stop Recording
          </button>
          {partialText && (
            <span className="text-sm text-gray-400 italic truncate max-w-xs">
              {partialText}
            </span>
          )}
        </>
      ) : (
        <button
          onClick={startRecording}
          disabled={disabled}
          className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-14 0m14 0a7 7 0 00-14 0m14 0v1a7 7 0 01-14 0v-1m7 8v3m-4 0h8"
            />
          </svg>
          Speak
        </button>
      )}
    </div>
  );
}
