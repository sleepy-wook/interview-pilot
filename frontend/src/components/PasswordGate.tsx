"use client";

import { useState, useEffect, useCallback } from "react";
import { API_BASE } from "@/lib/constants";

const STORAGE_KEY = "interview-pilot-pw";

/** Returns the stored password (or empty string). */
export function getStoredPassword(): string {
  if (typeof window === "undefined") return "";
  return sessionStorage.getItem(STORAGE_KEY) || "";
}

interface Props {
  children: React.ReactNode;
}

export default function PasswordGate({ children }: Props) {
  const [checking, setChecking] = useState(true);
  const [required, setRequired] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [input, setInput] = useState("");
  const [error, setError] = useState("");

  // Check if auth is required
  useEffect(() => {
    fetch(`${API_BASE}/api/auth/check`)
      .then((r) => r.json())
      .then((data) => {
        setRequired(data.required);
        if (!data.required) {
          setAuthenticated(true);
        } else {
          // Try stored password
          const stored = getStoredPassword();
          if (stored) {
            verifyPassword(stored);
          }
        }
      })
      .catch(() => {
        // If check fails, assume no auth required
        setAuthenticated(true);
      })
      .finally(() => setChecking(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const verifyPassword = useCallback(
    async (pw: string) => {
      try {
        const res = await fetch(`${API_BASE}/api/interview/company-roles`, {
          headers: { "X-App-Password": pw },
        });
        if (res.ok) {
          sessionStorage.setItem(STORAGE_KEY, pw);
          setAuthenticated(true);
          setError("");
        } else {
          sessionStorage.removeItem(STORAGE_KEY);
          setError("Incorrect password");
        }
      } catch {
        setError("Cannot connect to server");
      }
    },
    []
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) verifyPassword(input.trim());
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-400 text-sm">Loading...</div>
      </div>
    );
  }

  if (!required || authenticated) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl shadow-lg p-8 w-full max-w-sm space-y-4"
      >
        <h1 className="text-xl font-semibold text-gray-800 text-center">
          Interview Pilot
        </h1>
        <p className="text-sm text-gray-500 text-center">
          Enter the access password to continue.
        </p>
        <input
          type="password"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Password"
          className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          autoFocus
        />
        {error && <p className="text-sm text-red-500 text-center">{error}</p>}
        <button
          type="submit"
          className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Enter
        </button>
      </form>
    </div>
  );
}
