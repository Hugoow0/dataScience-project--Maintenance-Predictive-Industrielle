export type ModelTaskType = "classification" | "multi_class" | "regression"

export interface HealthResponse {
  status: string
  models_loaded: string[]
}

export interface ModelInfoItem {
  model: string
  file_name: string
  task_type: ModelTaskType
  target_variable: string
  loaded: boolean
  aliases: string[]
  metrics: Record<string, number> | null
}

export interface ModelInfoResponse {
  models: ModelInfoItem[]
}

export interface PredictFeatureInput {
  machine_type?: string | null
  vibration_rms: number
  temperature_motor: number
  current_phase_avg: number
  pressure_level: number
  rpm: number
  operating_mode: string
  hours_since_maintenance: number
  ambient_temp: number
}

export interface PredictRequest {
  model: string
  features: PredictFeatureInput
}

export interface ClassificationPredictionResponse {
  task_type: "classification" | "multi_class"
  model: string
  prediction: number | string
  probability: number
  label: string
}

export interface RegressionPredictionResponse {
  task_type: "regression"
  model: string
  prediction: number
  unit: string
}

export type PredictResponse = ClassificationPredictionResponse | RegressionPredictionResponse

export interface ValueCount {
  count: number
  percentage: number
}

export interface HistogramBin {
  left: number
  right: number
  count: number
}

export interface NumericSummary {
  min: number
  max: number
  mean: number
  median: number
  std: number
  histogram: HistogramBin[]
}

export interface CorrelationPoint {
  x: string
  y: string
  value: number
}

export interface TimeSeriesPoint {
  timestamp: string
  vibration_rms: number
  temperature_motor: number
}

export interface DatasetStatsResponse {
  row_count: number
  column_count: number
  date_range: { start: string; end: string } | null
  class_balance: Record<string, number>
  numeric_summary: Record<string, NumericSummary>
  categorical_summary: Record<string, Record<string, ValueCount>>
  correlation_matrix: CorrelationPoint[]
  missing_values: Record<string, ValueCount>
  time_series_sample: TimeSeriesPoint[] | null
}

export interface ModelComparisonItem {
  model: string
  task_type: ModelTaskType
  target_variable: string
  file_name: string
  metrics: Record<string, number>
}

export interface ModelComparisonResponse {
  models: ModelComparisonItem[]
}

export interface ApiValidationError {
  loc: Array<string | number>
  msg: string
  type: string
}

export interface ApiErrorPayload {
  error: string
  detail: unknown
}
