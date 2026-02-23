"use client";

import { useEffect, useState } from "react";

interface Props {
  company: string;
  role: string;
}

const STEPS = [
  { label: "Searching for job description", agent: "Research Agent" },
  { label: "Analyzing job requirements", agent: "Research Agent" },
  { label: "Researching company information", agent: "Research Agent" },
  { label: "Checking interview reviews", agent: "Research Agent" },
  { label: "Analyzing competitive landscape", agent: "Research Agent" },
  { label: "Generating interview plan", agent: "Master Agent" },
];

export default function ResearchProgress({ company, role }: Props) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    // Simulate progress steps while backend processes
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < STEPS.length - 1) return prev + 1;
        return prev;
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Preparing Your Interview
          </h2>
          <p className="text-gray-500">
            Researching{" "}
            <span className="font-medium text-gray-700">{role}</span> at{" "}
            <span className="font-medium text-gray-700">{company}</span>
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          {/* Progress bar */}
          <div className="h-1.5 bg-gray-100 rounded-full mb-6 overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-1000 ease-out"
              style={{
                width: `${((currentStep + 1) / STEPS.length) * 100}%`,
              }}
            />
          </div>

          {/* Steps */}
          <div className="space-y-3">
            {STEPS.map((step, i) => (
              <div key={i} className="flex items-center gap-3">
                {/* Status icon */}
                <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                  {i < currentStep ? (
                    <svg
                      className="w-5 h-5 text-green-500"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  ) : i === currentStep ? (
                    <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <div className="w-3 h-3 bg-gray-200 rounded-full" />
                  )}
                </div>

                {/* Label */}
                <div className="flex-1">
                  <span
                    className={`text-sm ${
                      i <= currentStep
                        ? "text-gray-900"
                        : "text-gray-400"
                    }`}
                  >
                    {step.label}
                  </span>
                  {i === currentStep && (
                    <span className="text-xs text-gray-400 ml-2">
                      ({step.agent})
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="text-center text-xs text-gray-400 mt-4">
          This may take 30-60 seconds...
        </p>
      </div>
    </div>
  );
}
