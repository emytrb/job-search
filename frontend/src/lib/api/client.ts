// Dynamically determine API base URL based on current browser location
// This enables access via Tailscale or other remote connections
function getApiBase(): string {
  // Use environment variable if explicitly set
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }

  // In browser: use the same host as the frontend, but port 8000
  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location
    return `${protocol}//${hostname}:8000/api/v1`
  }

  // SSR fallback
  return "http://localhost:8000/api/v1"
}

const API_BASE = getApiBase()

export interface UserPreferences {
  id: number
  cv_text: string
  target_stack: string[]
  target_seniority: string
  target_location: string
  digest_enabled: boolean
  digest_hour_utc: number
  digest_email: string | null
  ats_guidelines: string
  job_requirements_context: string
  cover_letter_guidelines: string
  similarity_threshold: number
  sponsorship_bonus_threshold: number
  stale_task_timeout_minutes: number
}

export interface DigestPreview {
  job_count: number
  jobs: Array<{
    id: number
    title: string
    company: string
    score: number
  }>
}

export interface AnalyzeRequest {
  job_title: string
  company_name: string
  job_text: string
  job_url: string
}

export interface JobSummary {
  title: string
  company: string
  key_requirements: string[]
}

export interface ResumeSuggestion {
  section: string
  suggestion: string
  reason: string
}

export interface ATSKeyword {
  keyword: string
  found_in_resume: boolean
  importance: string
}

export interface AnalyzeResponse {
  eligibility_status: "eligible" | "partially_eligible" | "not_eligible"
  eligibility_reasons: string[]
  matching_score: number
  matching_explanation: string
  job_summary: JobSummary
  resume_suggestions: ResumeSuggestion[]
  ats_keywords: ATSKeyword[]
  cover_letter: string
  processing_time_ms: number
}

export interface SavedAnalysis {
  id: number
  job_title: string
  company_name: string
  job_description: string
  job_url: string | null
  eligibility_status: "eligible" | "partially_eligible" | "not_eligible"
  eligibility_reasons: string[]
  matching_score: number
  matching_explanation: string
  key_requirements: string[]
  resume_suggestions: ResumeSuggestion[]
  ats_keywords: ATSKeyword[]
  cover_letter: string
  processing_time_ms: number
  llm_model: string | null
  offers_sponsorship: boolean
  applied: boolean
  created_at: string
  last_analyzed_at: string
}

export interface SavedAnalysisListItem {
  id: number
  job_title: string
  company_name: string
  eligibility_status: "eligible" | "partially_eligible" | "not_eligible"
  matching_score: number
  offers_sponsorship: boolean
  applied: boolean
  created_at: string
  last_analyzed_at: string
}

export interface SavedAnalysisListResponse {
  analyses: SavedAnalysisListItem[]
  total: number
}

export interface QueueItem {
  id: number
  job_text_preview: string
  job_url: string
  status: "pending" | "processing" | "completed" | "failed"
  error_message: string | null
  retry_count: number
  max_retries: number
  saved_analysis_id: number | null
  job_title: string
  company_name: string
  matching_score: number | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface QueueStatusResponse {
  items: QueueItem[]
  pending_count: number
  processing_count: number
  completed_count: number
  failed_count: number
}

export interface QueueAddResponse {
  id: number
  status: string
  position: number
}

export interface RequeueResponse {
  queued_count: number
  queue_items: QueueAddResponse[]
}

export interface DuplicateCheckResponse {
  is_duplicate: boolean
  similarity_score: number
  matched_analysis_id: number | null
  matched_job_title: string | null
  matched_company_name: string | null
}

async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return response.json()
}

export const api = {
  digest: {
    preview: () => fetchApi<DigestPreview>("/digest/preview"),
    send: () => fetchApi<{ status: string; task_id: string }>("/digest/send", { method: "POST" }),
  },

  preferences: {
    get: () => fetchApi<UserPreferences>("/preferences"),
    update: (data: Partial<UserPreferences>) =>
      fetchApi<UserPreferences>("/preferences", { method: "PUT", body: JSON.stringify(data) }),
  },

  analyzer: {
    // Queue operations
    addToQueue: (data: AnalyzeRequest) =>
      fetchApi<QueueAddResponse>("/analyzer/analyze", { method: "POST", body: JSON.stringify(data) }),
    getQueue: () => fetchApi<QueueStatusResponse>("/analyzer/queue"),
    removeFromQueue: (id: number) =>
      fetchApi<{ status: string }>(`/analyzer/queue/${id}`, { method: "DELETE" }),
    retryQueueItem: (id: number) =>
      fetchApi<{ status: string; id: number }>(`/analyzer/queue/${id}/retry`, { method: "POST" }),

    // Saved analyses
    list: (params?: { limit?: number; offset?: number; applied?: boolean | null }) => {
      const searchParams = new URLSearchParams()
      if (params?.limit) searchParams.set("limit", params.limit.toString())
      if (params?.offset) searchParams.set("offset", params.offset.toString())
      if (params?.applied !== undefined && params?.applied !== null) {
        searchParams.set("applied", params.applied.toString())
      } else if (params?.applied === null) {
        // null means "both" - don't send the param so backend returns all
      }
      const query = searchParams.toString()
      return fetchApi<SavedAnalysisListResponse>(`/analyzer/saved${query ? `?${query}` : ""}`)
    },
    get: (id: number) => fetchApi<SavedAnalysis>(`/analyzer/saved/${id}`),
    delete: (id: number) => fetchApi<{ status: string }>(`/analyzer/saved/${id}`, { method: "DELETE" }),
    toggleApplied: (id: number) =>
      fetchApi<{ id: number; applied: boolean }>(`/analyzer/saved/${id}/applied`, { method: "PATCH" }),
    requeue: (analysisIds: number[]) =>
      fetchApi<RequeueResponse>("/analyzer/requeue", {
        method: "POST",
        body: JSON.stringify({ analysis_ids: analysisIds }),
      }),
    checkDuplicate: (jobText: string) =>
      fetchApi<DuplicateCheckResponse>("/analyzer/check-duplicate", {
        method: "POST",
        body: JSON.stringify({ job_text: jobText }),
      }),
  },
}
