"""
Battery Test Bench - Station Data Models
Version: 1.2.6

Changelog:
v1.2.6 (2026-02-16): Comprehensive BatteryConfig from CMM analysis (DIEHL 3301-31
                      + Cobham 301-3017); supports capacity test, fast discharge,
                      reconditioning, pass/fail criteria, multi-phase automation
v1.2.5 (2026-02-16): ManualControlCommand supports wait + voltage_min_mv
v1.2.2 (2026-02-16): BatteryConfig is now battery MODEL params from EEPROM
v1.0.1 (2026-02-12): Initial station models
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List
from datetime import datetime


class StationState(str, Enum):
    """Station state machine states"""
    EMPTY = "empty"
    DOCK_DETECTED = "dock_detected"
    READY = "ready"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


class BatteryType(int, Enum):
    """Battery types from EEPROM"""
    NICD = 0
    NIMH = 1
    LIFEPO4 = 2
    LIION = 3
    SLA = 4


class BatteryConfig(BaseModel):
    """
    Battery MODEL configuration from EEPROM (DS24B33 via RP2040).

    Derived from CMM analysis of DIEHL 3301-31 and Cobham 301-3017.
    The EEPROM on each battery dock stores all parameters needed for
    fully automated testing with zero user intervention beyond intake.
    Per-unit data (serial number, test history) is tracked in the database.
    """
    format_version: int = Field(..., description="EEPROM format version (2 = CMM-compliant)")
    battery_type: BatteryType = Field(..., description="Battery chemistry type")
    nominal_capacity_mah: int = Field(..., ge=0, description="Nominal capacity in mAh")
    cell_count: int = Field(default=1, ge=1, le=40, description="Number of cells in battery")
    nominal_voltage_mv: int = Field(default=6000, ge=0, le=30000, description="Nominal battery voltage in mV")

    # Standard charge parameters (CMM standard charge method)
    charge_voltage_limit_mv: int = Field(..., ge=0, le=20000, description="Charge voltage limit in mV")
    standard_charge_current_ma: int = Field(..., ge=0, le=10000, description="Standard charge current in mA")
    standard_charge_duration_min: int = Field(default=960, ge=0, description="Standard charge time in minutes")

    # Reconditioning charge (for batteries stored > threshold months)
    recondition_charge_current_ma: int = Field(default=0, ge=0, le=10000, description="Reconditioning charge current in mA")
    recondition_charge_duration_min: int = Field(default=840, ge=0, description="Reconditioning charge time in minutes")
    recondition_storage_threshold_months: int = Field(default=6, ge=0, description="Storage months triggering reconditioning")

    # Trickle charge (for storage maintenance)
    trickle_charge_current_ma: int = Field(default=0, ge=0, le=5000, description="Trickle charge current in mA")

    # Capacity test discharge
    cap_test_discharge_current_ma: int = Field(..., ge=0, le=10000, description="Capacity test discharge current in mA")
    cap_test_end_voltage_mv: int = Field(..., ge=0, description="Capacity test end-of-discharge voltage in mV")
    cap_test_max_duration_min: int = Field(default=480, ge=0, description="Max capacity test discharge time in minutes")
    cap_test_rest_before_min: int = Field(default=240, ge=0, description="Rest period after charge before capacity test (min)")

    # Capacity pass/fail criteria
    cap_test_pass_min_minutes: int = Field(default=0, ge=0, description="Min discharge time for pass (0=not used)")
    cap_test_pass_min_capacity_pct: int = Field(default=0, ge=0, le=100, description="Min capacity % for pass (0=not used)")
    cap_test_voltage_check_time_min: int = Field(default=0, ge=0, description="Time to check voltage during discharge (0=not used)")
    cap_test_voltage_check_min_mv: int = Field(default=0, ge=0, description="Min voltage at check time in mV (0=not used)")

    # Fast discharge test (optional - e.g., Cobham 301-3017)
    fast_discharge_enabled: bool = Field(default=False, description="Fast discharge test enabled")
    fast_discharge_current_ma: int = Field(default=0, ge=0, le=30000, description="Fast discharge current in mA")
    fast_discharge_end_voltage_mv: int = Field(default=0, ge=0, description="Fast discharge end voltage in mV")
    fast_discharge_pass_min_minutes: int = Field(default=0, ge=0, description="Min time for fast discharge pass")
    fast_discharge_rest_before_min: int = Field(default=60, ge=0, description="Rest after charge before fast discharge (min)")

    # Pre-discharge (residual discharge before starting charge)
    pre_discharge_current_ma: int = Field(default=0, ge=0, le=30000, description="Pre-discharge current in mA (0=use cap_test current)")
    pre_discharge_end_voltage_mv: int = Field(default=0, ge=0, description="Pre-discharge end voltage in mV (0=use cap_test value)")

    # Post-test partial charge (for storage/delivery)
    post_charge_enabled: bool = Field(default=True, description="Partial charge after test for delivery")
    post_charge_duration_min: int = Field(default=270, ge=0, description="Post-test charge duration in minutes")

    # Temperature limits
    max_charge_temp_c: float = Field(default=45.0, description="Max temperature during charge in °C")
    max_discharge_temp_c: float = Field(default=55.0, description="Max temperature during discharge in °C")
    emergency_temp_max_c: float = Field(default=60.0, description="Emergency shutdown temperature in °C")
    min_operating_temp_c: float = Field(default=-15.0, description="Min operating temperature in °C")

    # Safety
    absolute_min_voltage_mv: int = Field(default=4500, ge=0, description="Absolute min voltage — below this causes cell damage")

    # Age-based extended rest
    age_rest_threshold_months: int = Field(default=24, ge=0, description="Battery age (months) requiring extended rest")
    age_rest_duration_min: int = Field(default=1440, ge=0, description="Extended rest period for aged batteries (min)")

    # Model identification
    part_number: str = Field(default="", max_length=32, description="Battery part number")
    model_description: str = Field(default="", max_length=32, description="Battery model description")
    manufacturer_code: str = Field(default="", max_length=8, description="Manufacturer code (e.g., D1347, F6175)")


class StationStatus(BaseModel):
    """Real-time station status"""
    station_id: int = Field(..., ge=1, le=12, description="Station ID (1-12)")
    state: StationState = Field(..., description="Current state")

    # Temperature from RP2040 (MAX31820 via 1-Wire)
    temperature_c: Optional[float] = Field(None, description="Current temperature in °C (from RP2040)")
    temperature_valid: bool = Field(False, description="Temperature reading valid flag")

    # Voltage/current from Siglent SCPI equipment (NOT from RP2040)
    voltage_mv: Optional[int] = Field(None, description="Current voltage in mV (from SCPI)")
    current_ma: Optional[int] = Field(None, description="Current current in mA (from SCPI)")

    # EEPROM status (DS24B33 via RP2040)
    eeprom_present: bool = Field(False, description="EEPROM detected flag")

    error_message: Optional[str] = Field(None, description="Error message if in ERROR state")
    session_id: Optional[int] = Field(None, description="Active session ID")
    work_order_item_id: Optional[int] = Field(None, description="Active work order item ID")
    test_phase: Optional[str] = Field(None, description="Current test phase")
    elapsed_time_s: Optional[float] = Field(None, description="Elapsed time in current step")
    battery_config: Optional[BatteryConfig] = Field(None, description="Battery model config from EEPROM")


class Station(BaseModel):
    """Complete station data model"""
    status: StationStatus
    battery_config: Optional[BatteryConfig] = None
    last_update: datetime = Field(default_factory=datetime.now)


class ManualControlCommand(BaseModel):
    """Manual control command for a station"""
    station_id: int = Field(..., ge=1, le=12)
    command: str = Field(..., description="Command: 'charge', 'discharge', 'wait', 'stop'")
    voltage_mv: Optional[int] = Field(None, ge=0, le=20000, description="Charge voltage limit in mV")
    current_ma: Optional[int] = Field(None, ge=0, le=10000, description="Target current in mA")
    voltage_min_mv: Optional[int] = Field(None, ge=0, le=20000, description="End-of-discharge voltage in mV")
    duration_min: Optional[int] = Field(None, ge=1, le=2880, description="Wait duration in minutes")


class RecipeStartCommand(BaseModel):
    """Start recipe test command"""
    station_id: int = Field(..., ge=1, le=12)
    recipe_id: int = Field(..., description="Recipe ID to execute")
    notes: Optional[str] = Field(None, description="Session notes")
