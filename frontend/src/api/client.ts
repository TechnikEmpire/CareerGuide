export type RetrievedChunk = {
  chunk_id?: string | null;
  chunk_type?: string | null;
  source_name: string;
  source_url: string;
  title: string;
  text: string;
  score: number;
  dense_score?: number | null;
  rerank_score?: number | null;
};

export type AnswerResponse = {
  answer: string;
  citations: RetrievedChunk[];
  prompt_preview: string;
  memory_summary: string;
  response_kind?: string;
};

export type CareerPlanStep = {
  title: string;
  description: string;
  focus_skills: string[];
  grounded_detail?: string | null;
  estimated_hours?: number | null;
};

export type StudyPreferences = {
  study_start_date?: string | null;
  preferred_study_time: string;
  study_frequency_per_week: number;
  session_duration_minutes: number;
  timezone: string;
};

export type CareerPlanCalendarEvent = {
  title: string;
  description: string;
  starts_at: string;
  ends_at: string;
  week_index: number;
  step_index: number;
  session_index: number;
  total_sessions: number;
};

export type CareerPlanResponse = {
  goal: string;
  target_role: string;
  workload_level: string;
  estimated_weeks: number;
  study_preferences: StudyPreferences;
  steps: CareerPlanStep[];
  calendar_events: CareerPlanCalendarEvent[];
  citations: RetrievedChunk[];
};

export type MemoryItemPayload = {
  id: string;
  user_id: string;
  text: string;
  category: string;
  importance: number;
  confidence: number;
};

type ErrorPayload = {
  detail?: string;
};

const DEFAULT_DEV_API_BASE_URL = "http://127.0.0.1:8000";

function resolveApiBaseUrl(): string {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL;
  if (configuredBaseUrl && configuredBaseUrl.trim()) {
    return configuredBaseUrl.replace(/\/+$/, "");
  }
  if (import.meta.env.DEV) {
    return DEFAULT_DEV_API_BASE_URL;
  }
  return "";
}

const apiBaseUrl = resolveApiBaseUrl();

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as ErrorPayload;
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Ignore malformed error bodies and surface the status instead.
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export function getApiBaseUrl(): string {
  return apiBaseUrl;
}

export function requestAnswer(userId: string, question: string): Promise<AnswerResponse> {
  return requestJson<AnswerResponse>("/chat/answer", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      question,
    }),
  });
}

export function requestCareerPlan(
  userId: string,
  goal: string,
  targetRole: string,
  studyPreferences: StudyPreferences,
): Promise<CareerPlanResponse> {
  return requestJson<CareerPlanResponse>("/career/plan", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      goal,
      target_role: targetRole,
      study_preferences: studyPreferences,
    }),
  });
}

export async function exportCareerPlanIcs(userId: string, plan: CareerPlanResponse): Promise<{ blob: Blob; fileName: string }> {
  const response = await fetch(`${apiBaseUrl}/career/plan/export-ics`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
      plan,
    }),
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as ErrorPayload;
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Ignore malformed error bodies and surface the status instead.
    }
    throw new Error(detail);
  }

  const contentDisposition = response.headers.get("content-disposition") ?? "";
  const fileNameMatch = contentDisposition.match(/filename=\"([^\"]+)\"/i);
  return {
    blob: await response.blob(),
    fileName: fileNameMatch?.[1] ?? "career-plan.ics",
  };
}

export function fetchMemories(userId: string): Promise<MemoryItemPayload[]> {
  const params = new URLSearchParams({ user_id: userId });
  return requestJson<MemoryItemPayload[]>(`/memory/list?${params.toString()}`);
}

export function deleteMemory(userId: string, memoryId: string): Promise<MemoryItemPayload> {
  const params = new URLSearchParams({ user_id: userId });
  return requestJson<MemoryItemPayload>(`/memory/${encodeURIComponent(memoryId)}?${params.toString()}`, {
    method: "DELETE",
  });
}
