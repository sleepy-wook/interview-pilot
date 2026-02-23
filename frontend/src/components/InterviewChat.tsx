"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import type {
  ChatMessage as ChatMessageType,
  AnswerAnalysis,
  Persona,
  HintData,
} from "@/lib/types";
import { getNextQuestion, submitAnswer } from "@/lib/api";
import ChatMessage from "./ChatMessage";
import HintPanel from "./HintPanel";
import VoiceRecorder from "./VoiceRecorder";
import CoachingPanel from "./CoachingPanel";

interface Props {
  sessionId: string;
  totalQuestions: number;
  mode: "practice" | "real";
  vocabularyName?: string;
  onInterviewEnd: () => void;
}

export default function InterviewChat({
  sessionId,
  totalQuestions,
  mode,
  vocabularyName,
  onInterviewEnd,
}: Props) {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [inputText, setInputText] = useState("");
  const [inputMode, setInputMode] = useState<"voice" | "text">("voice");
  const [loading, setLoading] = useState(false);
  const [currentHints, setCurrentHints] = useState<HintData | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [lastAnalysis, setLastAnalysis] = useState<AnswerAnalysis | null>(null);
  const [lastPersona, setLastPersona] = useState<Persona | null>(null);
  const [isDone, setIsDone] = useState(false);
  const [currentPersona, setCurrentPersona] = useState<Persona | null>(null);
  const [currentQuestionText, setCurrentQuestionText] = useState("");
  const [voiceTranscript, setVoiceTranscript] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasFetchedFirst = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch first question on mount (guard against Strict Mode double-fire)
  useEffect(() => {
    if (hasFetchedFirst.current) return;
    hasFetchedFirst.current = true;
    fetchNextQuestion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchNextQuestion = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getNextQuestion(sessionId);
      if (res.done) {
        setIsDone(true);
        return;
      }
      if (res.question && res.persona) {
        const msg: ChatMessageType = {
          id: `q-${Date.now()}`,
          role: "interviewer",
          persona: res.persona,
          text: res.question,
          topic: res.topic,
          hints: res.hints,
        };
        setMessages((prev) => [...prev, msg]);
        setCurrentHints(res.hints || null);
        setCurrentPersona(res.persona);
        setCurrentQuestionText(res.question);
        setCurrentQuestion((prev) => prev + 1);
      }
    } catch (err) {
      console.error("Failed to get next question:", err);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleSubmitAnswer = useCallback(
    async (answerText: string, voiceMetrics?: Record<string, unknown>) => {
      if (!answerText.trim() || loading) return;

      // Add user message
      const userMsg: ChatMessageType = {
        id: `a-${Date.now()}`,
        role: "user",
        text: answerText,
      };
      setMessages((prev) => [...prev, userMsg]);
      setInputText("");
      setVoiceTranscript("");
      setCurrentHints(null);
      setLoading(true);

      try {
        const res = await submitAnswer(sessionId, {
          answer: answerText,
          voice_metrics: voiceMetrics,
        });

        // Update user message with analysis
        setMessages((prev) =>
          prev.map((m) =>
            m.id === userMsg.id ? { ...m, analysis: res.analysis } : m
          )
        );
        setLastAnalysis(res.analysis);
        setLastPersona(currentPersona);

        if (res.is_interview_over) {
          setIsDone(true);
        } else {
          // Fetch next question
          await fetchNextQuestion();
        }
      } catch (err) {
        console.error("Failed to submit answer:", err);
      } finally {
        setLoading(false);
      }
    },
    [sessionId, loading, currentPersona, fetchNextQuestion]
  );

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmitAnswer(inputText);
  };

  const handleVoiceDone = (
    transcript: string,
    voiceMetrics: Record<string, unknown>
  ) => {
    handleSubmitAnswer(transcript, voiceMetrics);
  };

  const handleVoiceTranscript = (text: string, isFinal: boolean) => {
    if (isFinal) {
      setVoiceTranscript((prev) => prev + " " + text);
    } else {
      setVoiceTranscript(text);
    }
  };

  if (isDone) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Interview Complete
          </h2>
          <p className="text-gray-500 mb-6">
            You answered {currentQuestion} questions. Let&apos;s see your
            evaluation report.
          </p>
          <button
            onClick={onInterviewEnd}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            View Report
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex min-h-0">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-1">
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {/* Hint panel for current question */}
          {currentHints && mode === "practice" && (
            <div className="ml-2">
              <HintPanel hints={currentHints} disabled={loading} />
            </div>
          )}

          {/* Loading indicator */}
          {loading && (
            <div className="flex justify-start mb-4">
              <div className="px-4 py-3 bg-gray-100 rounded-2xl rounded-bl-md">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  />
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="border-t border-gray-200 p-4 bg-white">
          {/* Voice transcript preview */}
          {voiceTranscript && inputMode === "voice" && (
            <div className="mb-2 p-2 bg-gray-50 rounded-lg text-sm text-gray-600 italic">
              {voiceTranscript}
            </div>
          )}

          <div className="flex items-center gap-2">
            {/* Mode toggle */}
            <div className="flex bg-gray-100 rounded-lg p-0.5">
              <button
                onClick={() => setInputMode("voice")}
                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                  inputMode === "voice"
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500"
                }`}
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
              </button>
              <button
                onClick={() => setInputMode("text")}
                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                  inputMode === "text"
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500"
                }`}
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
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
              </button>
            </div>

            {/* Input */}
            {inputMode === "voice" ? (
              <VoiceRecorder
                onTranscript={handleVoiceTranscript}
                onDone={handleVoiceDone}
                onError={(msg) => console.error("Voice error:", msg)}
                vocabularyName={vocabularyName}
                disabled={loading}
              />
            ) : (
              <form onSubmit={handleTextSubmit} className="flex-1 flex gap-2">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Type your answer..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-gray-900"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !inputText.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                >
                  Send
                </button>
              </form>
            )}
          </div>
        </div>
      </div>

      {/* Coaching side panel */}
      <CoachingPanel
        currentQuestion={currentQuestion}
        totalQuestions={totalQuestions}
        lastAnalysis={lastAnalysis}
        lastPersona={lastPersona}
      />
    </div>
  );
}
