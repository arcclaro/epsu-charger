"""
Battery Test Bench - Automated Test Rule Engine
Version: 2.0.0

Changelog:
v2.0.0 (2026-02-22): Major refactor — generate_test_plan() now delegates to
                      ProcedureResolver for data-driven procedure resolution.
                      Removed hardcoded _has_heating_foil(), _determine_manual_tests(),
                      _build_capacity_test_sequence(), _build_charge_only_sequence().
                      Kept: ServiceType enum, get_example_configs(), ManualTestInput,
                      AutomatedTestPlan (for backward compat), TestSequenceStep.
v1.2.7 (2026-02-16): Initial rule engine; auto-generates CMM-compliant test
                      sequences from EEPROM BatteryConfig + work order metadata

Service types supported:
- CAPACITY_TEST:  Full CMM capacity test
- RECONDITIONING: Extended reconditioning for long-stored batteries
- FAST_DISCHARGE: High-rate discharge test (e.g., Cobham 301-3017)
- CHARGE_ONLY:   Standard charge for storage/delivery
- FULL_SERVICE:   Reconditioning + capacity test + fast discharge (all applicable)

NOTE: As of v2.0.0, procedure steps are data-driven via tech_pub_sections +
procedure_steps tables. The ProcedureResolver replaces the hardcoded step-building
logic. This module retains the ServiceType enum, dataclasses, and example configs
for backward compatibility and EEPROM programming reference.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

from models.station import BatteryConfig
from services.eeprom_manager import build_test_params_from_eeprom
from services.test_controller import TestParameters

logger = logging.getLogger(__name__)


class ServiceType(str, Enum):
    """Work order service types that the system can automate"""
    CAPACITY_TEST = "capacity_test"
    RECONDITIONING = "reconditioning"
    FAST_DISCHARGE = "fast_discharge"
    CHARGE_ONLY = "charge_only"
    FULL_SERVICE = "full_service"


@dataclass
class ManualTestInput:
    """
    Non-energy test results collected via PWA forms.
    These are NOT automated by the test bench — the technician
    performs them manually and enters results for report generation.
    """
    # Insulation test (CMM: 500VDC megohmmeter, >2 MOhm pass)
    insulation_test_performed: bool = False
    insulation_resistance_mohm: Optional[float] = None
    insulation_test_voltage_vdc: int = 500
    insulation_pass: Optional[bool] = None

    # Heating foil resistance (DIEHL 3214-31: 14.4 Ohm +/- 20%)
    heating_foil_test_performed: bool = False
    heating_foil_resistance_ohm: Optional[float] = None
    heating_foil_pass: Optional[bool] = None

    # Temperature sensor resistance (DIEHL 3214-31: NTC check)
    temp_sensor_test_performed: bool = False
    temp_sensor_resistance_kohm: Optional[float] = None
    temp_sensor_pass: Optional[bool] = None

    # Thermostat test
    thermostat_test_performed: bool = False
    thermostat_open_temp_c: Optional[float] = None
    thermostat_close_temp_c: Optional[float] = None
    thermostat_pass: Optional[bool] = None

    # Visual inspection
    visual_inspection_performed: bool = False
    visual_inspection_notes: Optional[str] = None
    visual_inspection_pass: Optional[bool] = None

    # Weight check
    weight_check_performed: bool = False
    weight_kg: Optional[float] = None
    weight_pass: Optional[bool] = None

    # Technician notes
    technician_notes: Optional[str] = None


@dataclass
class TestSequenceStep:
    """A single step in the generated test sequence"""
    phase: str
    description: str
    estimated_duration_min: float
    automated: bool = True


@dataclass
class AutomatedTestPlan:
    """Complete test plan generated from EEPROM + work order"""
    service_type: ServiceType
    battery_config: BatteryConfig
    test_params: TestParameters
    steps: List[TestSequenceStep] = field(default_factory=list)
    estimated_total_hours: float = 0.0
    needs_reconditioning: bool = False
    needs_fast_discharge: bool = False
    manual_tests_required: List[str] = field(default_factory=list)


def generate_test_plan(config: BatteryConfig,
                       service_type: ServiceType,
                       battery_age_months: int = 0,
                       months_since_last_service: int = 0,
                       battery_revision: str = "") -> AutomatedTestPlan:
    """
    Generate a test plan from EEPROM config + work order metadata.

    DEPRECATED in v2.0.0: This function is retained for backward compatibility.
    New code should use ProcedureResolver.resolve_procedure() which is fully
    data-driven (zero code changes to add new battery models).

    This legacy path still works by building TestParameters from EEPROM and
    creating a simplified step list. For full CMM-compliant procedure resolution
    including manual tests and conditional sections, use the ProcedureResolver.
    """
    # Build TestParameters from EEPROM config + age rules
    force_reconditioning = service_type in (ServiceType.RECONDITIONING,
                                            ServiceType.FULL_SERVICE)
    effective_months = months_since_last_service
    if force_reconditioning and effective_months < config.recondition_storage_threshold_months:
        effective_months = config.recondition_storage_threshold_months

    params = build_test_params_from_eeprom(
        config=config,
        battery_age_months=battery_age_months,
        months_since_last_service=effective_months,
    )

    # Override fast discharge based on service type
    if service_type in (ServiceType.FAST_DISCHARGE, ServiceType.FULL_SERVICE):
        params.fast_discharge_enabled = config.fast_discharge_enabled
    elif service_type == ServiceType.CHARGE_ONLY:
        params.fast_discharge_enabled = False

    plan = AutomatedTestPlan(
        service_type=service_type,
        battery_config=config,
        test_params=params,
        steps=[],
        estimated_total_hours=0.0,
        needs_reconditioning=params.needs_reconditioning,
        needs_fast_discharge=params.fast_discharge_enabled,
        manual_tests_required=[],
    )

    logger.info(
        f"Legacy test plan generated: {config.part_number} / {service_type.value} "
        f"(use ProcedureResolver for full data-driven procedures)"
    )

    return plan


def get_example_configs() -> dict:
    """
    Return example EEPROM configurations for the three analyzed battery models.
    Useful for testing and for programming new dock EEPROMs.
    """
    return {
        "DIEHL_3301_31": {
            "format_version": 2,
            "battery_type": 0,  # NiCd
            "nominal_capacity_mah": 1700,
            "cell_count": 5,
            "nominal_voltage_mv": 6000,
            "charge_voltage_limit_mv": 9000,
            "standard_charge_current_ma": 400,
            "standard_charge_duration_min": 270,  # 4.5h
            "trickle_charge_current_ma": 0,
            "recondition_charge_current_ma": 0,
            "recondition_charge_duration_min": 0,
            "recondition_storage_threshold_months": 0,
            "cap_test_discharge_current_ma": 5000,  # ~5A via 1.2 Ohm equiv
            "cap_test_end_voltage_mv": 5000,
            "cap_test_max_duration_min": 60,
            "cap_test_rest_before_min": 240,  # 4h
            "cap_test_pass_min_minutes": 0,  # Uses curve shape
            "cap_test_pass_min_capacity_pct": 80,
            "cap_test_voltage_check_time_min": 0,
            "cap_test_voltage_check_min_mv": 0,
            "fast_discharge_enabled": False,
            "pre_discharge_current_ma": 0,
            "pre_discharge_end_voltage_mv": 0,
            "post_charge_enabled": True,
            "post_charge_duration_min": 270,  # 4.5h
            "max_charge_temp_c": 45.0,
            "max_discharge_temp_c": 55.0,
            "emergency_temp_max_c": 60.0,
            "min_operating_temp_c": -15.0,
            "absolute_min_voltage_mv": 4500,
            "age_rest_threshold_months": 24,
            "age_rest_duration_min": 1440,  # 24h
            "part_number": "3301-31",
            "model_description": "DIEHL NiCd 6V 1.7Ah",
            "manufacturer_code": "D1347",
        },
        "COBHAM_301_3017": {
            "format_version": 2,
            "battery_type": 0,  # NiCd
            "nominal_capacity_mah": 2300,
            "cell_count": 5,
            "nominal_voltage_mv": 6000,
            "charge_voltage_limit_mv": 9000,
            "standard_charge_current_ma": 230,  # C/10
            "standard_charge_duration_min": 960,  # 16h
            "trickle_charge_current_ma": 0,
            "recondition_charge_current_ma": 230,
            "recondition_charge_duration_min": 840,  # 14h
            "recondition_storage_threshold_months": 6,
            "cap_test_discharge_current_ma": 460,  # C/5
            "cap_test_end_voltage_mv": 5000,
            "cap_test_max_duration_min": 480,  # 8h max
            "cap_test_rest_before_min": 60,
            "cap_test_pass_min_minutes": 240,  # 4h at C/5
            "cap_test_pass_min_capacity_pct": 80,
            "cap_test_voltage_check_time_min": 0,
            "cap_test_voltage_check_min_mv": 0,
            "fast_discharge_enabled": True,
            "fast_discharge_current_ma": 4000,
            "fast_discharge_end_voltage_mv": 5000,
            "fast_discharge_pass_min_minutes": 15,  # ~15min at 4A
            "fast_discharge_rest_before_min": 60,
            "pre_discharge_current_ma": 460,  # C/5
            "pre_discharge_end_voltage_mv": 5000,
            "post_charge_enabled": True,
            "post_charge_duration_min": 960,  # Full 16h charge after test
            "max_charge_temp_c": 45.0,
            "max_discharge_temp_c": 55.0,
            "emergency_temp_max_c": 60.0,
            "min_operating_temp_c": -18.0,
            "absolute_min_voltage_mv": 4500,
            "age_rest_threshold_months": 24,
            "age_rest_duration_min": 1440,
            "part_number": "301-3017",
            "model_description": "Cobham NiCd 6V 2.3Ah",
            "manufacturer_code": "F6175",
        },
        "DIEHL_3214_31": {
            "format_version": 2,
            "battery_type": 0,  # NiCd
            "nominal_capacity_mah": 4000,  # AMDT-/A/B; 5000 for AMDT C+
            "cell_count": 5,
            "nominal_voltage_mv": 6000,
            "charge_voltage_limit_mv": 9000,
            "standard_charge_current_ma": 400,  # C/10
            "standard_charge_duration_min": 960,  # 16h
            "trickle_charge_current_ma": 40,  # C/100
            "recondition_charge_current_ma": 400,
            "recondition_charge_duration_min": 840,
            "recondition_storage_threshold_months": 6,
            "cap_test_discharge_current_ma": 800,  # C/5
            "cap_test_end_voltage_mv": 5000,
            "cap_test_max_duration_min": 480,
            "cap_test_rest_before_min": 240,  # 4h standard
            "cap_test_pass_min_minutes": 0,
            "cap_test_pass_min_capacity_pct": 80,
            "cap_test_voltage_check_time_min": 0,
            "cap_test_voltage_check_min_mv": 0,
            "fast_discharge_enabled": False,
            "pre_discharge_current_ma": 800,
            "pre_discharge_end_voltage_mv": 5000,
            "post_charge_enabled": True,
            "post_charge_duration_min": 270,
            "max_charge_temp_c": 45.0,
            "max_discharge_temp_c": 55.0,
            "emergency_temp_max_c": 60.0,
            "min_operating_temp_c": -15.0,
            "absolute_min_voltage_mv": 4500,
            "age_rest_threshold_months": 24,
            "age_rest_duration_min": 1440,
            "part_number": "3214-31",
            "model_description": "DIEHL NiCd 6V 4Ah",
            "manufacturer_code": "D1347",
        },
    }
