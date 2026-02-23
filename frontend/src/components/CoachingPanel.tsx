"use client";

import type { AnswerAnalysis, Persona } from "@/lib/types";
import { PERSONA_CONFIG } from "@/lib/constants";

interface Props {
  currentQuestion: number;
  totalQuestions: number;
  lastAnalysis: AnswerAnalysis | null;
  lastPersona: Persona | null;
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color =
    value >= 70 ? "#059669" : value >= 40 ? "#d97706" : "#dc2626";

  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-0.5">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium" style={{ color }}>
          {value}%
        </span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export default function CoachingPanel({
  currentQuestion,
  totalQuestions,
  lastAnalysis,
  lastPersona,
}: Props) {
  const pConfig = lastPersona ? PERSONA_CONFIG[lastPersona] : null;

  return (
    <div className="w-72 border-l border-gray-200 bg-gray-50 p-4 overflow-y-auto flex-shrink-0 hidden lg:block">
      {/* Progress */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Progress</h3>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-300"
              style={{
                width: `${Math.min(totalQuestions > 0 ? (currentQuestion / totalQuestions) * 100 : 0, 100)}%`,
              }}
            />
          </div>
          <span className="text-xs text-gray-500 font-medium whitespace-nowrap">
            {currentQuestion}{currentQuestion > totalQuestions ? `/${totalQuestions}+` : `/${totalQuestions}`}
          </span>
        </div>
      </div>

      {/* Last answer analysis */}
      {lastAnalysis ? (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-sm font-medium text-gray-700">
              Last Answer
            </h3>
            {pConfig && (
              <span
                className="text-xs px-1.5 py-0.5 rounded font-medium"
                style={{
                  backgroundColor: pConfig.bgColor,
                  color: pConfig.color,
                }}
              >
                {pConfig.icon} {lastPersona}
              </span>
            )}
          </div>

          <ScoreBar label="Specificity" value={lastAnalysis.specificity_score} />
          <ScoreBar label="STAR" value={lastAnalysis.star_score} />
          <ScoreBar label="Confidence" value={lastAnalysis.confidence_score} />

          {/* Flags */}
          {lastAnalysis.flags && lastAnalysis.flags.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-gray-600 mb-1">Flags:</p>
              <div className="flex flex-wrap gap-1">
                {lastAnalysis.flags.map((f, i) => (
                  <span
                    key={i}
                    className="text-xs px-1.5 py-0.5 bg-red-50 text-red-600 rounded"
                  >
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Summary */}
          {lastAnalysis.summary && (
            <div className="mt-3 p-2 bg-white rounded border border-gray-200">
              <p className="text-xs text-gray-600">{lastAnalysis.summary}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="text-sm text-gray-400 text-center mt-8">
          Answer a question to see real-time coaching feedback
        </div>
      )}
    </div>
  );
}
