from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class SensorReadings(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """Current sensor readings for a zone/chamber."""
    temp: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Relative humidity percentage")
    ph: float = Field(..., description="pH level of the nutrient solution")
    ec: float = Field(..., description="Electrical conductivity in mS/cm")
    soil_moisture: List[float] = Field(..., description="List of soil moisture percentages from multiple sensors")
    tank_level_pct: float = Field(..., description="Water tank level percentage")

class MLResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """Machine learning inference results for a specific plant."""
    plant_id: int = Field(..., description="Unique identifier for the plant")
    ripeness: str = Field(..., description="Ripeness classification (e.g., 'unripe', 'ripe', 'overripe')")
    disease: Optional[str] = Field(None, description="Detected disease classification, if any")
    confidence: float = Field(..., description="Confidence score of the ML prediction (0.0 to 1.0)")

class PollinationWindow(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """Configuration for a plant's pollination window."""
    start_hour: int = Field(..., description="Start hour of the pollination window (0-23)")
    end_hour: int = Field(..., description="End hour of the pollination window (0-23)")
    interval_days: int = Field(..., description="Minimum days between pollinations")

class PlantProfile(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """Target environment and configuration for a specific plant species/profile."""
    id: int = Field(..., description="Unique identifier for the plant profile")
    name: str = Field(..., description="Common name of the plant")
    species: str = Field(..., description="Scientific or species name")
    moisture_target: float = Field(..., description="Target soil moisture percentage")
    ec_target: float = Field(..., description="Target electrical conductivity in mS/cm")
    ph_min: float = Field(..., description="Minimum acceptable pH level")
    ph_max: float = Field(..., description="Maximum acceptable pH level")
    pollination_window: Optional[PollinationWindow] = Field(None, description="Time window and interval for pollination")

class LightPeriod(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """A time period when grow lights are active."""
    start_hour: int = Field(..., description="Start hour of the light period (0-23)")
    end_hour: int = Field(..., description="End hour of the light period (0-23)")
    intensity_pct: int = Field(..., description="Light intensity percentage (0-100)")

class QueueState(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """Current state of pending operations."""
    harvest_pending_ids: List[int] = Field(..., description="List of plant IDs pending harvest")
    active_harvest_id: Optional[int] = Field(None, description="Plant ID currently being harvested")

class SystemConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """Global system configuration and operational parameters."""
    maintenance_mode: bool = Field(..., description="Whether the system is in maintenance mode")
    zone_count: int = Field(..., description="Number of independent control zones")
    max_pump_time_s: int = Field(..., description="Maximum allowed pump run time in seconds")
    temp_min: float = Field(18.0, description="Minimum allowed temperature")
    temp_max: float = Field(30.0, description="Maximum allowed temperature")
    light_schedule: List[LightPeriod] = Field(default_factory=list, description="Schedule for the lighting system")

class History(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """Historical operation records."""
    last_watering: Dict[int, datetime] = Field(..., description="Mapping of zone/chamber ID to last watering timestamp")
    last_pollination: Optional[datetime] = Field(None, description="Timestamp of the last pollination event")

class Position(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """3D position coordinates."""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    z: float = Field(..., description="Z coordinate")

class SensorSnapshot(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """Lightweight sensor snapshot for event-driven decisions."""
    ec: float = Field(..., description="Electrical conductivity in mS/cm")
    ph: float = Field(..., description="pH level")
    water_temp: float = Field(..., description="Water temperature in Celsius")
    air_temp: float = Field(..., description="Air temperature in Celsius")
    air_humidity: float = Field(..., description="Air humidity percentage")

class PlantTarget(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """Plant targeting information for lightweight payload."""
    plant_id: int = Field(..., description="Unique plant ID")
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    z: float = Field(..., description="Z coordinate")
    ec_target: float = Field(..., description="Target EC")
    ph_target: float = Field(..., description="Target pH")

class StateSnapshot(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """Complete representation of the system state at a specific point in time."""
    # Legacy fields
    sensor_readings: Optional[SensorReadings] = Field(None, description="Current sensor readings")
    ml_results: Optional[List[MLResult]] = Field(None, description="Machine learning inference results")
    plant_profiles: Optional[List[PlantProfile]] = Field(None, description="Target environment and configuration")
    queue_state: Optional[QueueState] = Field(None, description="Current state of pending operations")
    system_config: Optional[SystemConfig] = Field(None, description="Global system configuration")
    history: Optional[History] = Field(None, description="Historical operation records")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of this state snapshot")

    # Lightweight event context fields
    trigger_event: Optional[str] = Field(None, description="Event that triggered this evaluation")
    tool_state: Optional[str] = Field(None, description="Current active tool attached to the arm")
    current_position: Optional[Position] = Field(None, description="Current position of the arm")
    sensor_snapshot: Optional[SensorSnapshot] = Field(None, description="Sensor snapshot values")
    plant_targets: Optional[List[PlantTarget]] = Field(None, description="Targets related to plants")
    harvest_queue: Optional[List[int]] = Field(None, description="Queue of plant IDs to harvest")
    last_watered_at: Optional[datetime] = Field(None, description="Timestamp when last watered")
