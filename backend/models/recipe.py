"""
Battery Test Bench - Recipe Models
Version: 1.0.1

Changelog:
v1.0.1 (2026-02-12): Initial recipe models
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class StepType(str, Enum):
    """Recipe step types"""
    CHARGE = "charge"
    DISCHARGE = "discharge"
    REST = "rest"
    WAIT_TEMP = "wait_temp"


class StopCondition(str, Enum):
    """Step stop conditions"""
    VOLTAGE = "voltage"
    CURRENT = "current"
    TIME = "time"
    TEMPERATURE = "temperature"
    CAPACITY = "capacity"


class RecipeStep(BaseModel):
    """Single step in a test recipe"""
    step_number: int = Field(..., ge=1, description="Step sequence number")
    step_type: StepType = Field(..., description="Type of step")

    # Charging/Discharging parameters
    voltage_mv: Optional[int] = Field(None, ge=0, le=20000, description="Target/limit voltage in mV")
    current_ma: Optional[int] = Field(None, ge=0, le=10000, description="Target/limit current in mA")

    # Stop conditions
    stop_condition: StopCondition = Field(..., description="Primary stop condition")
    stop_value: float = Field(..., description="Stop condition value")

    # Optional secondary limits
    max_time_s: Optional[int] = Field(None, ge=1, description="Maximum step duration in seconds")
    max_voltage_mv: Optional[int] = Field(None, description="Maximum voltage limit")
    min_voltage_mv: Optional[int] = Field(None, description="Minimum voltage limit")
    max_current_ma: Optional[int] = Field(None, description="Maximum current limit")
    max_temperature_c: Optional[float] = Field(None, description="Maximum temperature limit")

    description: Optional[str] = Field(None, description="Step description")


class Recipe(BaseModel):
    """Test recipe definition"""
    id: Optional[int] = Field(None, description="Recipe ID (auto-generated)")
    name: str = Field(..., min_length=1, max_length=100, description="Recipe name")
    description: Optional[str] = Field(None, description="Recipe description")
    steps: List[RecipeStep] = Field(..., min_items=1, max_items=20, description="Recipe steps")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Standard Charge/Discharge Cycle",
                "description": "Full charge followed by discharge to 80% DOD",
                "steps": [
                    {
                        "step_number": 1,
                        "step_type": "charge",
                        "voltage_mv": 4200,
                        "current_ma": 1000,
                        "stop_condition": "voltage",
                        "stop_value": 4200,
                        "max_time_s": 14400,
                        "description": "CC-CV charge to 4.2V"
                    },
                    {
                        "step_number": 2,
                        "step_type": "rest",
                        "stop_condition": "time",
                        "stop_value": 600,
                        "description": "10-minute rest"
                    },
                    {
                        "step_number": 3,
                        "step_type": "discharge",
                        "current_ma": 500,
                        "stop_condition": "voltage",
                        "stop_value": 3000,
                        "max_time_s": 14400,
                        "description": "Constant current discharge to 3.0V"
                    }
                ]
            }
        }


class RecipeCreate(BaseModel):
    """Recipe creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    steps: List[RecipeStep] = Field(..., min_items=1, max_items=20)


class RecipeUpdate(BaseModel):
    """Recipe update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    steps: Optional[List[RecipeStep]] = Field(None, min_items=1, max_items=20)
