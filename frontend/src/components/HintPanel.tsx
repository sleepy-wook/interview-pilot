"use client";

import { useState } from "react";
import type { HintData } from "@/lib/types";

interface Props {
  hints: HintData;
  disabled?: boolean;
  onReveal?: () => void;
}

export default function HintPanel({ hints, disabled, onReveal }: Props) {
  const [open, setOpen] = useState(false);
  const [showExample, setShowExample] = useState(false);

  if (!hints?.bullets?.length && !hints?.personal_hooks?.length) return null;

  const handleToggle = () => {
    if (!open && onReveal) onReveal();
    setOpen(!open);
  };

  return (
    <div className="mt-2">
      <button
        onClick={handleToggle}
        disabled={disabled}
        className={`flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg transition-colors ${
          open
            ? "bg-amber-50 text-amber-700 border border-amber-200"
            : "bg-gray-50 text-gray-500 hover:bg-gray-100 border border-transparent"
        } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        <span>{"\u{1F4A1}"}</span>
        <span>{open ? "Hide Hints" : "Show Hints"}</span>
      </button>

      <div className={`collapsible ${open ? "open" : ""}`}>
        <div>
          <div className="mt-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm">
            {hints.bullets && hints.bullets.length > 0 && (
              <div className="mb-2">
                <p className="font-medium text-amber-800 mb-1">Key Points:</p>
                <ul className="list-disc list-inside space-y-0.5 text-amber-900">
                  {hints.bullets.map((b, i) => (
                    <li key={i}>{b}</li>
                  ))}
                </ul>
              </div>
            )}

            {hints.personal_hooks && hints.personal_hooks.length > 0 && (
              <div className="mb-2">
                <p className="font-medium text-amber-800 mb-1">
                  From Your Resume:
                </p>
                <ul className="list-disc list-inside space-y-0.5 text-amber-900">
                  {hints.personal_hooks.map((h, i) => (
                    <li key={i}>{h}</li>
                  ))}
                </ul>
              </div>
            )}

            {hints.avoid && hints.avoid.length > 0 && (
              <div className="mb-2">
                <p className="font-medium text-red-700 mb-1">Avoid:</p>
                <ul className="list-disc list-inside space-y-0.5 text-red-600">
                  {hints.avoid.map((a, i) => (
                    <li key={i}>{a}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Progressive hint: example answer */}
            {hints.example_answer && (
              <div className="mt-2 pt-2 border-t border-amber-200">
                {!showExample ? (
                  <button
                    onClick={() => setShowExample(true)}
                    className="text-xs text-amber-600 hover:text-amber-800 font-medium transition-colors"
                  >
                    Still stuck? Show example answer &rarr;
                  </button>
                ) : (
                  <div>
                    <p className="font-medium text-amber-800 mb-1 text-xs">
                      Example Answer:
                    </p>
                    <p className="text-amber-900 whitespace-pre-line leading-relaxed">
                      {hints.example_answer}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
