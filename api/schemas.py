from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class OperatingMode(str, Enum):
    idle = "idle"
    normal = "normal"
    high_load = "high_load"

class SensorInput(BaseModel):
    machine_id: int
    machine_type: str
    vibration_rms: float = Field(..., description="Niveau de vibration RMS")
    temperature_motor: float = Field(..., description="Température du moteur en °C")
    current_phase_avg: Optional[float] = None
    pressure_level: Optional[float] = None
    rpm: float
    operating_mode: OperatingMode
    hours_since_maintenance: float
    ambient_temp: float

class PredictionOutput(BaseModel):
    prediction: int
    probability: float
