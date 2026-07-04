from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class OperatingMode(str, Enum):
    idle = "idle"
    normal = "normal"
    peak = "peak"


class MachineType(str, Enum):
    CNC = "CNC"
    Compressor = "Compressor"
    Pump = "Pump"
    Robotic_Arm = "Robotic Arm"


class TaskType(str, Enum):
    classification = "classification"
    multi_class = "multi_class"
    regression = "regression"


class FeatureInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    machine_type: Optional[MachineType] = Field(default=None)
    vibration_rms: float = Field(..., gt=0.0)
    temperature_motor: float = Field(..., ge=-20.0, le=200.0)
    current_phase_avg: float = Field(..., ge=0.0)
    pressure_level: float = Field(..., ge=0.0)
    rpm: float = Field(..., ge=0.0, le=20000.0)
    operating_mode: OperatingMode
    hours_since_maintenance: float = Field(..., ge=0.0)
    ambient_temp: float = Field(..., ge=-50.0, le=100.0)


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(..., min_length=1)
    features: FeatureInput


class ClassificationPredictionResponse(BaseModel):
    task_type: Literal["classification", "multi_class"]
    model: str
    prediction: int | str
    probability: float
    label: str


class RegressionPredictionResponse(BaseModel):
    task_type: Literal["regression"]
    model: str
    prediction: float
    unit: str


class HealthResponse(BaseModel):
    status: str
    models_loaded: list[str]


class DateRange(BaseModel):
    start: str
    end: str


class ValueCount(BaseModel):
    count: int
    percentage: float


class HistogramBin(BaseModel):
    left: float
    right: float
    count: int


class NumericSummary(BaseModel):
    min: float
    max: float
    mean: float
    median: float
    std: float
    histogram: list[HistogramBin]


class CorrelationPoint(BaseModel):
    x: str
    y: str
    value: float


class TimeSeriesPoint(BaseModel):
    timestamp: str
    vibration_rms: float
    temperature_motor: float


class DatasetStatsResponse(BaseModel):
    row_count: int
    column_count: int
    date_range: DateRange | None
    class_balance: dict[str, float]
    numeric_summary: dict[str, NumericSummary]
    categorical_summary: dict[str, dict[str, ValueCount]]
    correlation_matrix: list[CorrelationPoint]
    missing_values: dict[str, ValueCount]
    time_series_sample: list[TimeSeriesPoint] | None


class ModelMetricSet(BaseModel):
    model: str
    task_type: TaskType
    target_variable: str
    file_name: str
    metrics: dict[str, float]


class ModelInfoItem(BaseModel):
    model: str
    file_name: str
    task_type: TaskType
    target_variable: str
    loaded: bool
    aliases: list[str]
    metrics: dict[str, float] | None = None


class ModelInfoResponse(BaseModel):
    models: list[ModelInfoItem]


class ModelComparisonResponse(BaseModel):
    models: list[ModelMetricSet]


class ErrorResponse(BaseModel):
    error: str
    detail: Any