import { API_BASE } from "./constants";
import type {
  StartRequest,
  StartResponse,
  PlanResponse,
  NextQuestionResponse,
  AnswerRequest,
  AnswerResponse,
  EvaluationReport,
  HistoryResponse,
  CompanyRolesResponse,
} from "./types";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}/api/interview${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export function startInterview(data: StartRequest): Promise<StartResponse> {
  return request("/start", { method: "POST", body: JSON.stringify(data) });
}

export function getPlan(sessionId: string): Promise<PlanResponse> {
  return request(`/${sessionId}/plan`);
}

export function getNextQuestion(
  sessionId: string
): Promise<NextQuestionResponse> {
  return request(`/${sessionId}/next`);
}

export function submitAnswer(
  sessionId: string,
  data: AnswerRequest
): Promise<AnswerResponse> {
  return request(`/${sessionId}/answer`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function evaluateInterview(
  sessionId: string
): Promise<EvaluationReport> {
  return request(`/${sessionId}/evaluate`, { method: "POST" });
}

// ── History ──

export function getHistory(): Promise<HistoryResponse> {
  return request("/history");
}

// ── Company Roles ──

export function getCompanyRoles(): Promise<CompanyRolesResponse> {
  return request("/company-roles");
}

// ── File upload ──

export async function uploadFile(
  file: File
): Promise<{ filename: string; path: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Upload error ${res.status}: ${body}`);
  }
  return res.json();
}

// ── WebSocket for voice ──

export function createVoiceSocket(
  vocabularyName?: string
): WebSocket {
  const wsBase = API_BASE.replace(/^http/, "ws");
  const params = vocabularyName ? `?vocabulary=${vocabularyName}` : "";
  return new WebSocket(`${wsBase}/api/ws/voice${params}`);
}
