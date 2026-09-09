from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field, field_validator
import math

class DetectionSource(str, Enum):
    NEO6M = "NEO6M"
    PHONE_GPS = "PHONE_GPS"
    CONNECTED_GPS = "CONNECTED_GPS"
    CAMERA = "CAMERA"
    FUSED = "FUSED"
    SIMULATED = "SIMULATED"

class RiskLevel(str, Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class GPSState(BaseModel):
    vehicle_id: str
    source: DetectionSource
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    altitude_m: float | None = None
    speed_mps: float | None = Field(default=None, ge=0, le=150)
    heading_deg: float | None = Field(default=None, ge=0, lt=360)
    accuracy_m: float | None = Field(default=None, ge=0)
    timestamp: float
    satellites: int = Field(default=0, ge=0, le=99)
    fix: bool = True

    @field_validator("timestamp")
    @classmethod
    def finite_timestamp(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("timestamp must be finite")
        return value

class CameraDetection(BaseModel):
    detection_id: str
    object_class: Literal["car", "truck", "bus", "motorcycle", "bicycle", "person"] = Field(alias="class")
    confidence: float = Field(ge=0, le=1)
    bbox: dict[str, float]
    timestamp: float
    estimated_distance_m: float | None = Field(default=None, ge=0)
    model_config = {"populate_by_name": True}

class IMUState(BaseModel):
    acceleration_mps2: float = 0
    longitudinal_mps2: float = 0
    lateral_mps2: float = 0
    gyro_dps: tuple[float, float, float] = (0, 0, 0)
    sudden_braking: bool = False
    sharp_turn: bool = False
    timestamp: float = 0

class RiskMetrics(BaseModel):
    distance_m: float
    bearing_deg: float
    relative_bearing_deg: float
    closing_speed_mps: float
    ttc_s: float | None
    score: float = Field(ge=0, le=1)
    level: RiskLevel

class UnifiedVehicleState(BaseModel):
    vehicle_id: str
    vehicle_type: str = "car"
    latitude: float
    longitude: float
    speed_mps: float | None
    heading_deg: float | None
    distance_m: float
    bearing_deg: float
    relative_bearing_deg: float
    source: DetectionSource
    confidence: float = Field(ge=0, le=1)
    risk: RiskLevel
    risk_metrics: RiskMetrics
    updated_at: float
    accuracy_m: float | None = None
    status: str = "LIVE"

class WorldState(BaseModel):
    type: str = "world_state"
    host_vehicle: GPSState
    vehicles: list[UnifiedVehicleState]
    camera_detections: list[CameraDetection] = []
    imu: IMUState = IMUState()
    system_status: dict[str, str | int | float | bool]
    mode: str = "LIVE"
    scenario: str | None = None
    demo_running: bool = False
