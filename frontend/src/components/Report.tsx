"use client";

import { useState } from "react";
import type {
  EvaluationReport,
  PerQuestionEval,
  ModelAnswer,
} from "@/lib/types";
import { PERSONA_CONFIG, QUALITY_CONFIG } from "@/lib/constants";

interface Props {
  report: EvaluationReport;
  onRestart: () => void;
}

// ── Score Ring ──

function ScoreRing({
  score,
  size = 120,
  label,
}: {
  score: number;
  size?: number;
  label?: string;
}) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 70 ? "#059669" : score >= 40 ? "#d97706" : "#dc2626";

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#f3f4f6"
          strokeWidth={8}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="score-ring"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ width: size, height: size }}>
        <span className="text-2xl font-bold" style={{ color }}>
          {score}
        </span>
        <span className="text-xs text-gray-400">/100</span>
      </div>
      {label && (
        <span className="text-xs text-gray-500 mt-1 font-medium">{label}</span>
      )}
    </div>
  );
}

// ── Collapsible Section ──

function Section({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
      >
        <span className="font-medium text-gray-900">{title}</span>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      <div className={`collapsible ${open ? "open" : ""}`}>
        <div>
          <div className="p-4">{children}</div>
        </div>
      </div>
    </div>
  );
}

// ── Question Detail Card ──

function QuestionCard({ q }: { q: PerQuestionEval }) {
  const pConfig = PERSONA_CONFIG[q.persona];
  const qConfig = QUALITY_CONFIG[q.quality] || QUALITY_CONFIG.adequate;
  const starParts = [q.star.situation, q.star.task, q.star.action, q.star.result];

  return (
    <div className="border border-gray-200 rounded-lg p-4 mb-3">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span
            className="text-xs font-medium px-2 py-0.5 rounded"
            style={{ backgroundColor: pConfig.bgColor, color: pConfig.color }}
          >
            {pConfig.icon} {q.persona}
          </span>
          <span className="text-xs text-gray-400">Q{q.turn_number}</span>
          {q.hint_used && (
            <span className="text-xs px-1.5 py-0.5 bg-amber-50 text-amber-600 rounded">
              Hint used
            </span>
          )}
        </div>
        <span
          className="text-xs font-medium px-2 py-0.5 rounded"
          style={{ backgroundColor: qConfig.bgColor, color: qConfig.color }}
        >
          {qConfig.label}
        </span>
      </div>

      <p className="text-sm text-gray-900 mb-2">{q.question}</p>
      <p className="text-sm text-gray-500 italic mb-3">{q.answer_preview}</p>

      {/* Scores */}
      <div className="grid grid-cols-3 gap-2 mb-2">
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="text-lg font-bold text-gray-900">
            {q.confidence_score}
          </div>
          <div className="text-xs text-gray-500">Confidence</div>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="text-lg font-bold text-gray-900">
            {q.specificity_score}
          </div>
          <div className="text-xs text-gray-500">Specificity</div>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="text-lg font-bold text-gray-900">
            {q.star.score}
          </div>
          <div className="text-xs text-gray-500">STAR</div>
        </div>
      </div>

      {/* STAR breakdown */}
      <div className="flex gap-1 mb-2">
        {["S", "T", "A", "R"].map((letter, i) => (
          <span
            key={letter}
            className={`text-xs px-2 py-0.5 rounded font-mono ${
              starParts[i]
                ? "bg-green-50 text-green-700"
                : "bg-gray-100 text-gray-400"
            }`}
          >
            {letter}
          </span>
        ))}
        {q.star.feedback && (
          <span className="text-xs text-gray-400 ml-2 self-center">
            {q.star.feedback}
          </span>
        )}
      </div>

      {/* Flags */}
      {q.flags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {q.flags.map((f, i) => (
            <span
              key={i}
              className="text-xs px-1.5 py-0.5 bg-red-50 text-red-600 rounded"
            >
              {f}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Model Answer Card ──

function ModelAnswerCard({ ma }: { ma: ModelAnswer }) {
  const qConfig = QUALITY_CONFIG[ma.original_quality] || QUALITY_CONFIG.adequate;

  return (
    <div className="border border-gray-200 rounded-lg p-4 mb-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs text-gray-400">Q{ma.turn_number}</span>
        <span
          className="text-xs font-medium px-2 py-0.5 rounded"
          style={{ backgroundColor: qConfig.bgColor, color: qConfig.color }}
        >
          {qConfig.label}
        </span>
        <span className="text-xs text-gray-400">
          {ma.score_before} &rarr; {ma.score_after}
        </span>
      </div>

      <p className="text-sm font-medium text-gray-900 mb-2">{ma.question}</p>

      <div className="p-3 bg-green-50 border border-green-200 rounded-lg mb-2">
        <p className="text-xs font-medium text-green-800 mb-1">
          Improved Answer:
        </p>
        <p className="text-sm text-green-900 leading-relaxed">
          {ma.improved_answer}
        </p>
      </div>

      {ma.tips.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-600 mb-1">Tips:</p>
          <ul className="list-disc list-inside text-xs text-gray-600 space-y-0.5">
            {ma.tips.map((tip, i) => (
              <li key={i}>{tip}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ── Main Report ──

export default function Report({ report, onRestart }: Props) {
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-1">
            Interview Report
          </h1>
          <p className="text-sm text-gray-500">
            Comprehensive evaluation of your mock interview
          </p>
        </div>

        {/* Overall Score */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6 flex flex-col items-center">
          <div className="relative">
            <ScoreRing score={report.overall_score} size={140} />
          </div>
          <h2 className="text-lg font-bold text-gray-900 mt-2">
            Overall Score
          </h2>

          {/* Persona scores */}
          <div className="flex gap-6 mt-4">
            {Object.entries(report.persona_scores).map(([persona, score]) => {
              const pConfig =
                PERSONA_CONFIG[persona as keyof typeof PERSONA_CONFIG];
              if (!pConfig) return null;
              return (
                <div key={persona} className="text-center">
                  <div className="relative">
                    <ScoreRing score={score as number} size={80} />
                  </div>
                  <span
                    className="text-xs font-medium mt-1 block"
                    style={{ color: pConfig.color }}
                  >
                    {pConfig.icon} {persona}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Strengths & Weaknesses */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="bg-white border border-gray-200 rounded-xl p-4">
            <h3 className="font-medium text-green-700 mb-3">Strengths</h3>
            <ul className="space-y-2">
              {report.strengths.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-green-500 mt-0.5 flex-shrink-0">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </span>
                  <span className="text-gray-700">{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-4">
            <h3 className="font-medium text-amber-700 mb-3">
              Needs Improvement
            </h3>
            <ul className="space-y-2">
              {report.weaknesses.map((w, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-amber-500 mt-0.5 flex-shrink-0">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </span>
                  <span className="text-gray-700">{w}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Hint Usage */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6">
          <h3 className="font-medium text-gray-900 mb-3">Hint Usage</h3>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-xl font-bold text-green-700">
                {report.hint_analysis.breakdown.no_hint_needed}
              </div>
              <div className="text-xs text-green-600">No hint needed</div>
            </div>
            <div className="text-center p-3 bg-amber-50 rounded-lg">
              <div className="text-xl font-bold text-amber-700">
                {report.hint_analysis.breakdown.hint_used_answered_well}
              </div>
              <div className="text-xs text-amber-600">
                Hint used, answered well
              </div>
            </div>
            <div className="text-center p-3 bg-red-50 rounded-lg">
              <div className="text-xl font-bold text-red-700">
                {report.hint_analysis.breakdown.hint_used_still_weak}
              </div>
              <div className="text-xs text-red-600">
                Hint used, still weak
              </div>
            </div>
          </div>
          {report.hint_analysis.focus_topics.length > 0 && (
            <p className="text-sm text-gray-600">
              <span className="font-medium">Focus areas:</span>{" "}
              {report.hint_analysis.focus_topics.join(", ")}
            </p>
          )}
        </div>

        {/* Voice Metrics */}
        {report.voice_summary.has_voice_data && (
          <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6">
            <h3 className="font-medium text-gray-900 mb-3">Voice Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-900">
                  {report.voice_summary.avg_response_latency_s ?? "N/A"}s
                </div>
                <div className="text-xs text-gray-500">Avg Response Time</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-900">
                  {report.voice_summary.avg_filler_rate_per_min ?? 0}/min
                </div>
                <div className="text-xs text-gray-500">Filler Rate</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-900">
                  {report.voice_summary.total_filler_count ?? 0}
                </div>
                <div className="text-xs text-gray-500">Total Fillers</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-900">
                  {report.voice_summary.avg_answer_duration_s ?? 0}s
                </div>
                <div className="text-xs text-gray-500">Avg Duration</div>
              </div>
            </div>
            {report.voice_summary.shortest_answer && (
              <p className="text-sm text-gray-500 mt-2">
                Shortest answer: Q{report.voice_summary.shortest_answer.turn_number} (
                {report.voice_summary.shortest_answer.duration_s}s) &mdash;{" "}
                {report.voice_summary.shortest_answer.question_preview}
              </p>
            )}
          </div>
        )}

        {/* Collapsible sections */}
        <div className="space-y-3 mb-6">
          <Section title="Per-question Detail">
            {report.per_question.map((q) => (
              <QuestionCard key={q.turn_number} q={q} />
            ))}
          </Section>

          <Section title="Model Answers">
            {report.model_answers.length > 0 ? (
              report.model_answers.map((ma) => (
                <ModelAnswerCard key={ma.turn_number} ma={ma} />
              ))
            ) : (
              <p className="text-sm text-gray-500">
                All answers were strong — no model answers needed!
              </p>
            )}
          </Section>

          <Section title="Action Plan" defaultOpen>
            <ol className="space-y-2">
              {report.action_plan.map((item, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <span className="w-5 h-5 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <span className="text-gray-700">{item}</span>
                </li>
              ))}
            </ol>
          </Section>
        </div>

        {/* Restart button */}
        <div className="text-center">
          <button
            onClick={onRestart}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            Start New Interview
          </button>
        </div>
      </div>
    </div>
  );
}
