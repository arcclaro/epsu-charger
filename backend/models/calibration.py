"""
Battery Test Bench - Calibration Models
Version: 1.0.1

Changelog:
v1.0.1 (2026-02-12): Initial calibration models
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, timedelta


class Calibration(BaseModel):
    """Calibration tracking record"""
    id: Optional[int] = Field(None, description="Record ID")
    station_id: int = Field(..., ge=1, le=12, description="Station ID")
    calibration_date: date = Field(..., description="Date of calibration")
    next_calibration_date: date = Field(..., description="Next calibration due date")
    calibrated_by: Optional[str] = Field(None, description="Person who performed calibration")
    notes: Optional[str] = Field(None, description="Calibration notes")

    @property
    def is_due(self) -> bool:
        """Check if calibration is currently due"""
        return date.today() >= self.next_calibration_date

    @property
    def days_until_due(self) -> int:
        """Days until calibration is due (negative if overdue)"""
        return (self.next_calibration_date - date.today()).days


class CalibrationCreate(BaseModel):
    """Create/update calibration record"""
    station_id: int = Field(..., ge=1, le=12)
    calibration_date: date = Field(default_factory=date.today)
    calibration_interval_days: int = Field(default=365, ge=1, description="Days until next calibration")
    calibrated_by: Optional[str] = None
    notes: Optional[str] = None

    @property
    def next_calibration_date(self) -> date:
        """Calculate next calibration date"""
        return self.calibration_date + timedelta(days=self.calibration_interval_days)
