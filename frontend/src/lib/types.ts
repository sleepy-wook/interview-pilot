// ── Application Phase ──

export type Phase = "setup" | "researching" | "interview" | "report";

// ── API Request/Response Types ──

export interface StartRequest {
  company: string;
  role: string;
  resume_path?: string;
  linkedin_path?: string;
  linkedin_url?: string;
  mode: "practice" | "real";
  model?: "haiku" | "sonnet";
  question_count?: number;
}

export interface StartResponse {
  session_id: string;
  research_brief_summary: {
    company: string;
    gaps_count: number;
    keywords_count: number;
  };
  plan_length: number;
  vocabulary: { vocabulary_name: string; status: string } | null;
}

export interface PlanResponse {
  plan: PlanItem[];
}

export interface PlanItem {
  question: string;
  persona: Persona;
  topic: string;
  priority: string;
  depth: string;
}

export interface NextQuestionResponse {
  done: boolean;
  message?: string;
  question?: string;
  persona?: Persona;
  topic?: string;
  hints?: HintData;
}

export interface HintData {
  bullets?: string[];
  personal_hooks?: string[];
  avoid?: string[];
  example_answer?: string;
}

export interface AnswerRequest {
  answer: string;
  voice_metrics?: Record<string, unknown>;
}

export interface AnswerResponse {
  analysis: AnswerAnalysis;
  consistency: ConsistencyResult | null;
  routing: RoutingResult;
  turn_number: number;
  is_interview_over: boolean;
}

export interface AnswerAnalysis {
  quality: "strong" | "adequate" | "weak" | "evasive";
  confidence_score: number;
  specificity_score: number;
  star_score: number;
  key_points_covered?: string[];
  missing_points?: string[];
  flags?: string[];
  summary?: string;
}

export interface ConsistencyResult {
  consistent: boolean;
  contradictions?: { description: string; severity: string }[];
  concerns?: string[];
}

export interface RoutingResult {
  next_persona: Persona;
  action: string;
  reason: string;
  suggested_topic?: string;
}

export interface VoiceMetrics {
  response_latency_s: number | null;
  answer_duration_s: number;
  filler_count: number;
  filler_words?: string[];
  word_count: number;
  filler_rate_per_min: number;
}

// ── Evaluation Report Types ──

export interface EvaluationReport {
  overall_score: number;
  persona_scores: Record<string, number>;
  strengths: string[];
  weaknesses: string[];
  per_question: PerQuestionEval[];
  consistency: ConsistencyResult;
  hint_analysis: HintAnalysis;
  voice_summary: VoiceSummary;
  model_answers: ModelAnswer[];
  action_plan: string[];
}

export interface PerQuestionEval {
  turn_number: number;
  persona: Persona;
  question: string;
  answer_preview: string;
  quality: string;
  confidence_score: number;
  specificity_score: number;
  star: {
    score: number;
    situation: boolean;
    task: boolean;
    action: boolean;
    result: boolean;
    feedback: string;
  };
  flags: string[];
  hint_used: boolean;
}

export interface HintAnalysis {
  total_questions: number;
  hints_used: number;
  hints_not_used: number;
  breakdown: {
    no_hint_needed: number;
    hint_used_answered_well: number;
    hint_used_still_weak: number;
  };
  hint_usage_rate: number;
  focus_topics: string[];
}

export interface VoiceSummary {
  has_voice_data: boolean;
  avg_response_latency_s?: number | null;
  avg_filler_rate_per_min?: number;
  total_filler_count?: number;
  avg_answer_duration_s?: number;
  avg_word_count?: number;
  shortest_answer?: {
    turn_number: number;
    question_preview: string;
    duration_s: number;
  };
}

export interface ModelAnswer {
  turn_number: number;
  question: string;
  original_quality: string;
  improved_answer: string;
  reasoning: string[];
  tips: string[];
  score_before: number;
  score_after: number;
}

// ── History Types ──

export interface HistorySession {
  session_id: string;
  company: string;
  role: string;
  mode: "practice" | "real";
  model: "haiku" | "sonnet";
  status: "in_progress" | "completed";
  overall_score: number | null;
  question_count: number;
  turn_count: number;
  created_at: string | null;
  completed_at: string | null;
}

export interface HistoryResponse {
  sessions: HistorySession[];
}

// ── Company Role Types ──

export interface CompanyRoleOption {
  id: string;
  company: string;
  role: string;
}

export interface CompanyRolesResponse {
  company_roles: CompanyRoleOption[];
}

// ── Common Types ──

export type Persona = "HM" | "Tech" | "HR";

export interface ChatMessage {
  id: string;
  role: "interviewer" | "user";
  persona?: Persona;
  text: string;
  topic?: string;
  analysis?: AnswerAnalysis;
  hints?: HintData;
}
