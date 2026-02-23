"use client";

import { useState, useCallback } from "react";
import type { Phase, StartRequest, EvaluationReport } from "@/lib/types";
import { startInterview, evaluateInterview } from "@/lib/api";
import SetupForm from "@/components/SetupForm";
import ResearchProgress from "@/components/ResearchProgress";
import InterviewChat from "@/components/InterviewChat";
import Report from "@/components/Report";
import HistoryList from "@/components/HistoryList";

export default function Home() {
  const [phase, setPhase] = useState<Phase>("setup");
  const [loading, setLoading] = useState(false);

  // Session data
  const [sessionId, setSessionId] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [mode, setMode] = useState<"practice" | "real">("practice");
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [vocabularyName, setVocabularyName] = useState<string | undefined>();
  const [report, setReport] = useState<EvaluationReport | null>(null);

  // Phase 0: Start interview
  const handleStart = useCallback(async (data: StartRequest) => {
    setCompany(data.company);
    setRole(data.role);
    setMode(data.mode);
    setLoading(true);
    setPhase("researching");

    try {
      const res = await startInterview(data);
      setSessionId(res.session_id);
      setTotalQuestions(res.plan_length);
      setVocabularyName(res.vocabulary?.vocabulary_name);
      setPhase("interview");
    } catch (err) {
      console.error("Failed to start interview:", err);
      setPhase("setup");
      alert("Failed to start interview. Please check that the backend is running.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Phase 3: Generate report
  const handleInterviewEnd = useCallback(async () => {
    setLoading(true);
    try {
      const evalReport = await evaluateInterview(sessionId);
      setReport(evalReport);
      setPhase("report");
    } catch (err) {
      console.error("Failed to generate report:", err);
      alert("Failed to generate evaluation report.");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  // Restart
  const handleRestart = useCallback(() => {
    setPhase("setup");
    setSessionId("");
    setReport(null);
    setTotalQuestions(0);
    setVocabularyName(undefined);
  }, []);

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* History sidebar */}
      <HistoryList visible={phase === "setup"} />

      {/* Header - shown during interview and report */}
      {(phase === "interview" || phase === "report") && (
        <header className="border-b border-gray-200 px-4 py-3 flex items-center justify-between bg-white">
          <div className="flex items-center gap-3">
            <h1 className="font-bold text-gray-900">Interview Pilot</h1>
            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">
              {company} &middot; {role}
            </span>
          </div>
          <div className="flex items-center gap-3">
            {phase === "interview" && (
              <span className="text-xs text-gray-400">
                {mode === "practice" ? "Practice Mode" : "Real Mode"}
              </span>
            )}
            <button
              onClick={() => {
                if (confirm("Are you sure you want to exit? Your progress will be lost.")) {
                  handleRestart();
                }
              }}
              className="text-xs px-2.5 py-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
            >
              Exit
            </button>
          </div>
        </header>
      )}

      {/* Main content */}
      {phase === "setup" && (
        <SetupForm onStart={handleStart} loading={loading} />
      )}

      {phase === "researching" && (
        <ResearchProgress company={company} role={role} />
      )}

      {phase === "interview" && sessionId && (
        <InterviewChat
          sessionId={sessionId}
          totalQuestions={totalQuestions}
          mode={mode}
          vocabularyName={vocabularyName}
          onInterviewEnd={handleInterviewEnd}
        />
      )}

      {phase === "report" && report && (
        <Report report={report} onRestart={handleRestart} />
      )}

      {/* Loading overlay for evaluation */}
      {loading && phase === "report" && (
        <div className="fixed inset-0 bg-white/80 flex items-center justify-center z-50">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-sm text-gray-500">Generating evaluation report...</p>
          </div>
        </div>
      )}
    </div>
  );
}
