import type {
  ApiErrorPayload,
  DatasetStatsResponse,
  HealthResponse,
  ModelComparisonResponse,
  ModelInfoResponse,
  PredictRequest,
  PredictResponse,
} from "@/types/api"

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "")

export class ApiError extends Error {
  status: number
  payload: ApiErrorPayload | null

  constructor(message: string, status: number, payload: ApiErrorPayload | null) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.payload = payload
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    let payload: ApiErrorPayload | null = null
    try {
      payload = (await response.json()) as ApiErrorPayload
    } catch {
      const text = await response.text()
      payload = { error: "Request failed", detail: text }
    }

    throw new ApiError(payload.error ?? "Request failed", response.status, payload)
  }

  return (await response.json()) as T
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  modelInfo: () => request<ModelInfoResponse>("/model-info"),
  datasetStats: () => request<DatasetStatsResponse>("/dataset/stats"),
  modelComparison: () => request<ModelComparisonResponse>("/dataset/model-comparison"),
  predict: (payload: PredictRequest) =>
    request<PredictResponse>("/predict", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
}
