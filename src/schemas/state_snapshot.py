from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class SensorReadings(BaseModel):
    """Current sensor readings for a zone/chamber."""
    temp: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Relative humidity percentage")
    ph: float = Field(..., description="pH level of the nutrient solution")
    ec: float = Field(..., description="Electrical conductivity in mS/cm")
    soil_moisture: List[float] = Field(..., description="List of soil moisture percentages from multiple sensors")
    tank_level_pct: float = Field(..., description="Water tank level percentage")

class MLResult(BaseModel):
    """Machine learning inference results for a specific plant."""
    plant_id: int = Field(..., description="Unique identifier for the plant")
    ripeness: str = Field(..., description="Ripeness classification (e.g., 'unripe', 'ripe', 'overripe')")
    disease: Optional[str] = Field(None, description="Detected disease classification, if any")
    confidence: float = Field(..., description="Confidence score of the ML prediction (0.0 to 1.0)")

class PlantProfile(BaseModel):
    """Target environment and configuration for a specific plant species/profile."""
    id: int = Field(..., description="Unique identifier for the plant profile")
    name: str = Field(..., description="Common name of the plant")
    species: str = Field(..., description="Scientific or species name")
    moisture_target: float = Field(..., description="Target soil moisture percentage")
    ec_target: float = Field(..., description="Target electrical conductivity in mS/cm")
    ph_min: float = Field(..., description="Minimum acceptable pH level")
    ph_max: float = Field(..., description="Maximum acceptable pH level")
    pollination_window: str = Field(..., description="Time window for pollination (e.g., '10:00-14:00')")

class QueueState(BaseModel):
    """Current state of pending operations."""
    harvest_pending_ids: List[int] = Field(..., description="List of plant IDs pending harvest")
    active_harvest_id: Optional[int] = Field(None, description="Plant ID currently being harvested")
    active_waterings: List[int] = Field(default_factory=list, description="List of zone IDs currently being watered")

class SystemConfig(BaseModel):
    """Global system configuration and operational parameters."""
    maintenance_mode: bool = Field(..., description="Whether the system is in maintenance mode")
    zone_count: int = Field(..., description="Number of independent control zones")
    max_pump_time_s: int = Field(..., description="Maximum allowed pump run time in seconds")

class History(BaseModel):
    """Historical operation records."""
    last_watering: Dict[int, datetime] = Field(..., description="Mapping of zone/chamber ID to last watering timestamp")
    last_pollination: Optional[datetime] = Field(None, description="Timestamp of the last pollination event")

class StateSnapshot(BaseModel):
    """Complete representation of the system state at a specific point in time."""
    sensor_readings: SensorReadings
    ml_results: List[MLResult]
    plant_profiles: List[PlantProfile]
    queue_state: QueueState
    system_config: SystemConfig
    history: History
    timestamp: datetime = Field(..., description="Timestamp of this state snapshot")
