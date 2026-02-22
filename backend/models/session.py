"""
Battery Test Bench - Session Models
Version: 1.0.1

Changelog:
v1.0.1 (2026-02-12): Initial session models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SessionStatus(str, Enum):
    """Session status"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class SessionData(BaseModel):
    """Time-series data point for a session"""
    timestamp: datetime
    voltage_mv: int
    current_ma: int
    temperature_c: float
    step_number: int


class Session(BaseModel):
    """Test session record"""
    id: Optional[int] = Field(None, description="Session ID (auto-generated)")
    station_id: int = Field(..., ge=1, le=12, description="Station ID")
    recipe_id: Optional[int] = Field(None, description="Recipe ID")
    recipe_name: Optional[str] = Field(None, description="Recipe name snapshot")
    start_time: datetime = Field(default_factory=datetime.now, description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    status: SessionStatus = Field(default=SessionStatus.RUNNING, description="Session status")
    battery_serial: Optional[str] = Field(None, description="Battery serial number")
    notes: Optional[str] = Field(None, description="Session notes")

    # Summary statistics (calculated at end)
    total_charge_mah: Optional[float] = Field(None, description="Total charge transferred in mAh")
    total_discharge_mah: Optional[float] = Field(None, description="Total discharge transferred in mAh")
    average_temperature_c: Optional[float] = Field(None, description="Average temperature")
    peak_temperature_c: Optional[float] = Field(None, description="Peak temperature")
    duration_s: Optional[int] = Field(None, description="Total duration in seconds")
    efficiency_percent: Optional[float] = Field(None, description="Charge/discharge efficiency")

    error_message: Optional[str] = Field(None, description="Error message if failed")


class SessionSummary(BaseModel):
    """Session summary for list views"""
    id: int
    station_id: int
    recipe_name: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    status: SessionStatus
    battery_serial: Optional[str]
    duration_s: Optional[int]
    efficiency_percent: Optional[float]


class SessionDetail(Session):
    """Detailed session with time-series data"""
    data_points: List[SessionData] = Field(default_factory=list, description="Time-series data")
