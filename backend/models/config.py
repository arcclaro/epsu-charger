"""
Battery Test Bench - Configuration Models
Version: 1.0.1

Changelog:
v1.0.1 (2026-02-12): Initial configuration models
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ConfigKey(BaseModel):
    """Configuration key-value pair"""
    key: str = Field(..., description="Configuration key")
    value: str = Field(..., description="Configuration value (JSON string)")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class ConfigUpdate(BaseModel):
    """Configuration update request"""
    key: str = Field(..., description="Configuration key")
    value: str = Field(..., description="Configuration value (JSON string)")
