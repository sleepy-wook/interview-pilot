import type { Persona } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const PERSONA_CONFIG: Record<
  Persona,
  { label: string; color: string; bgColor: string; borderColor: string; icon: string }
> = {
  HM: {
    label: "Hiring Manager",
    color: "#2563eb",
    bgColor: "#eff6ff",
    borderColor: "#bfdbfe",
    icon: "\uD83D\uDC54", // necktie
  },
  Tech: {
    label: "Technical Lead",
    color: "#059669",
    bgColor: "#ecfdf5",
    borderColor: "#a7f3d0",
    icon: "\uD83D\uDD27", // wrench
  },
  HR: {
    label: "HR Partner",
    color: "#7c3aed",
    bgColor: "#f5f3ff",
    borderColor: "#c4b5fd",
    icon: "\uD83E\uDDD1\u200D\uD83D\uDCBC", // person in office
  },
};

export const QUALITY_CONFIG: Record<
  string,
  { label: string; color: string; bgColor: string }
> = {
  strong: { label: "Strong", color: "#059669", bgColor: "#ecfdf5" },
  adequate: { label: "Adequate", color: "#d97706", bgColor: "#fffbeb" },
  weak: { label: "Weak", color: "#dc2626", bgColor: "#fef2f2" },
  evasive: { label: "Evasive", color: "#dc2626", bgColor: "#fef2f2" },
};
