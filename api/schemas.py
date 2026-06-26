from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class OperatingMode(str, Enum):
    idle = "idle"
    normal = "normal"
    high_load = "high_load"

class SensorInput(BaseModel):
    machine_id: int = Field(..., gt=0)
    machine_type: str
    vibration_rms: float = Field(..., ge=0, le=50, description="Vibration en mm/s")
    temperature_motor: float = Field(..., ge=-20, le=200, description="Température du moteur en °C")
    current_phase_avg: Optional[float] = Field(None, ge=0)
    pressure_level: Optional[float] = Field(None, ge=0)
    rpm: float = Field(..., ge=0, le=15000)
    operating_mode: OperatingMode
    hours_since_maintenance: float = Field(..., ge=0)
    ambient_temp: float = Field(..., ge=-50, le=100)


class PredictionOutput(BaseModel):
    prediction: int
    probability: float
