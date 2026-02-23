"use client";

import { useEffect, useState } from "react";
import type { HistorySession } from "@/lib/types";
import { getHistory } from "@/lib/api";

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return null;
  const color =
    score >= 70 ? "text-green-700 bg-green-50" :
    score >= 40 ? "text-amber-700 bg-amber-50" :
    "text-red-700 bg-red-50";
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${color}`}>
      {score}
    </span>
  );
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface Props {
  visible?: boolean;
}

export default function HistoryList({ visible = true }: Props) {
  const [sessions, setSessions] = useState<HistorySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    getHistory()
      .then((res) => setSessions(res.sessions))
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      {/* Sidebar */}
      <div
        className={`fixed top-0 left-0 h-full bg-white border-r border-gray-200 shadow-lg z-40 transition-transform duration-300 ease-in-out ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
        style={{ width: 320 }}
      >
        {/* Sidebar header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <h2 className="text-sm font-semibold text-gray-900">Past Interviews</h2>
          <button
            onClick={() => setOpen(false)}
            className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
            aria-label="Close sidebar"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Sidebar content */}
        <div className="overflow-y-auto h-[calc(100%-49px)] p-3">
          {loading && (
            <p className="text-sm text-gray-400 text-center py-4">Loading...</p>
          )}
          {!loading && sessions.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-4">No history yet</p>
          )}
          {!loading && sessions.length > 0 && (
            <div className="space-y-2">
              {sessions.map((s) => (
                <div
                  key={s.session_id}
                  className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {s.company}
                    </span>
                    <ScoreBadge score={s.overall_score} />
                  </div>
                  <p className="text-xs text-gray-500 truncate mt-0.5">{s.role}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-xs text-gray-400">
                      {formatDate(s.created_at)}
                    </span>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      s.status === "completed"
                        ? "bg-green-50 text-green-600"
                        : "bg-yellow-50 text-yellow-600"
                    }`}>
                      {s.status === "completed" ? "Done" : "In Progress"}
                    </span>
                    <span className="text-xs text-gray-400">
                      {s.turn_count} Q&A
                    </span>
                    <span className="text-xs text-gray-400 capitalize">
                      {s.model}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 bg-black/20 z-30"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Toggle button (visible when sidebar is closed and on setup phase) */}
      {!open && visible && (
        <button
          onClick={() => setOpen(true)}
          className="fixed top-4 left-4 z-20 flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg shadow-sm text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
          aria-label="Open history sidebar"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
          History
          {!loading && sessions.length > 0 && (
            <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">
              {sessions.length}
            </span>
          )}
        </button>
      )}
    </>
  );
}
