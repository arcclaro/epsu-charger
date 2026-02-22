"""
Battery Test Bench - Database Seed Data
Version: 2.0.0

Changelog:
v2.0.0 (2026-02-22): Added tech_pub_applicability, tech_pub_sections,
                      procedure_steps seed data for all 3 CMMs;
                      battery_profiles feature_flags; tools.tool_id_display;
                      station_equipment from station_calibrations
v1.0.1 (2026-02-18): Station calibration seed data updated — 20-point readings per unit
v1.0.0 (2026-02-18): Initial seed data — 5 customers, 3 tech pubs, 7 profiles,
                      8 recipes, 6 tools, 12x2 station calibrations, 5 work orders
                      with 23 items, 3 work jobs with 8 tasks
"""

import json
import logging

log = logging.getLogger(__name__)


# =============================================================================
# CUSTOMERS (5 records)
# =============================================================================

SEED_CUSTOMERS = [
    {"id": 1, "name": "TAP Air Portugal", "customer_code": "TAP001",
     "contact_person": "Joao Silva", "email": "joao@tap.pt",
     "phone": "+351 21 841 5000", "address_line1": "Aeroporto de Lisboa, 1749-078 Lisboa",
     "notes": "Largest customer, quarterly capacity tests", "is_active": True,
     "created_at": "2025-06-15T10:00:00"},
    {"id": 2, "name": "SATA Air Azores", "customer_code": "SATA001",
     "contact_person": "Maria Santos", "email": "maria@sata.pt",
     "phone": "+351 296 209 720", "address_line1": "Aeroporto Joao Paulo II, Ponta Delgada",
     "notes": "Batteries shipped by inter-island cargo", "is_active": True,
     "created_at": "2025-08-20T14:30:00"},
    {"id": 3, "name": "Ryanair", "customer_code": "RYR001",
     "contact_person": "Patrick O'Brien", "email": "patrick@ryanair.com",
     "phone": "+353 1 945 1212", "address_line1": "Dublin Airport, Co. Dublin, Ireland",
     "notes": "New customer, first batch received Feb 2026", "is_active": True,
     "created_at": "2026-01-10T09:00:00"},
    {"id": 4, "name": "Portugalia Airlines", "customer_code": "PGA001",
     "contact_person": "Carlos Mendes", "email": "carlos.mendes@portugalia.pt",
     "phone": "+351 21 842 5500", "address_line1": "Aeroporto de Lisboa",
     "notes": "", "is_active": True,
     "created_at": "2025-11-01T11:00:00"},
    {"id": 5, "name": "EasyJet Portugal", "customer_code": "EZY001",
     "contact_person": "Sarah Mitchell", "email": "sarah.m@easyjet.com",
     "phone": "+44 1234 567890", "address_line1": "Lisbon Hub Office",
     "notes": "Account on hold - pending contract renewal", "is_active": False,
     "created_at": "2025-09-15T08:00:00"},
]


# =============================================================================
# TECH PUBS (3 records)
# =============================================================================

SEED_TECH_PUBS = [
    {"id": 1, "cmm_number": "33-51-01",
     "title": "Component Maintenance Manual - DIEHL NiCd Battery 3301-31",
     "revision": "Original", "revision_date": "2008-01-14",
     "applicable_part_numbers": ["3301-31"],
     "ata_chapter": "33-51", "issued_by": "DIEHL Aerospace GmbH",
     "notes": "Original issue", "is_active": True},
    {"id": 2, "cmm_number": "33-51-17",
     "title": "Component Maintenance Manual - DIEHL NiCd Battery 3214-31",
     "revision": "Revision 12", "revision_date": "2023-02-01",
     "applicable_part_numbers": ["3214-31"],
     "ata_chapter": "33-51", "issued_by": "DIEHL Aerospace GmbH",
     "notes": "Rev 12 dated 01 Feb 2023", "is_active": True},
    {"id": 3, "cmm_number": "33-51-22",
     "title": "Component Maintenance Manual - Cobham NiCd Battery 301-3017",
     "revision": "Revision 12", "revision_date": "2023-06-26",
     "applicable_part_numbers": ["301-3017"],
     "ata_chapter": "33-51", "issued_by": "Cobham Mission Systems",
     "notes": "Rev 12 dated 26 Jun 2023", "is_active": True},
]


# =============================================================================
# BATTERY PROFILES (7 records)
# =============================================================================

SEED_PROFILES = [
    {"id": 1, "part_number": "3301-31", "amendment": "",
     "description": "DIEHL NiCd 6V 1.7Ah EPSU Battery (Original)",
     "manufacturer": "DIEHL Aerospace GmbH", "manufacturer_code": "D1347",
     "nominal_voltage_v": 6.0, "capacity_ah": 1.7, "num_cells": 5, "chemistry": "NiCd",
     "std_charge_current_ma": 350, "std_charge_duration_h": 5.0,
     "std_charge_voltage_limit_mv": 8900, "cap_test_current_a": 5.0,
     "cap_test_voltage_min_mv": 5000, "cap_test_duration_min": 60,
     "pre_discharge_current_a": 5.0, "pre_discharge_end_voltage_mv": 5000,
     "post_charge_current_ma": 350, "post_charge_duration_h": 5.0,
     "rest_before_cap_test_min": 240,
     "fast_discharge_enabled": False,
     "max_temp_c": 45.0, "discharge_max_temp_c": 55.0, "emergency_temp_max_c": 60.0,
     "pass_min_minutes": 18, "pass_min_capacity_pct": 85,
     "is_active": True},
    {"id": 2, "part_number": "3301-31", "amendment": "A",
     "description": "DIEHL NiCd 6V 1.7Ah EPSU Battery",
     "manufacturer": "DIEHL Aerospace GmbH", "manufacturer_code": "D1347",
     "nominal_voltage_v": 6.0, "capacity_ah": 1.7, "num_cells": 5, "chemistry": "NiCd",
     "std_charge_current_ma": 400, "std_charge_duration_h": 4.5,
     "std_charge_voltage_limit_mv": 9000, "cap_test_current_a": 5.0,
     "cap_test_voltage_min_mv": 5000, "cap_test_duration_min": 60,
     "pre_discharge_current_a": 5.0, "pre_discharge_end_voltage_mv": 5000,
     "post_charge_current_ma": 400, "post_charge_duration_h": 4.5,
     "rest_before_cap_test_min": 240,
     "fast_discharge_enabled": False,
     "max_temp_c": 45.0, "discharge_max_temp_c": 55.0, "emergency_temp_max_c": 60.0,
     "pass_min_minutes": 18, "pass_min_capacity_pct": 90,
     "is_active": True},
    {"id": 3, "part_number": "3301-31", "amendment": "B",
     "description": "DIEHL NiCd 6V 1.7Ah EPSU Battery (Rev 2019)",
     "manufacturer": "DIEHL Aerospace GmbH", "manufacturer_code": "D1347",
     "nominal_voltage_v": 6.0, "capacity_ah": 1.7, "num_cells": 5, "chemistry": "NiCd",
     "std_charge_current_ma": 425, "std_charge_duration_h": 4.0,
     "std_charge_voltage_limit_mv": 9000, "cap_test_current_a": 5.0,
     "cap_test_voltage_min_mv": 5100, "cap_test_duration_min": 55,
     "pre_discharge_current_a": 5.0, "pre_discharge_end_voltage_mv": 5100,
     "post_charge_current_ma": 425, "post_charge_duration_h": 4.0,
     "rest_before_cap_test_min": 180,
     "fast_discharge_enabled": False,
     "max_temp_c": 45.0, "discharge_max_temp_c": 55.0, "emergency_temp_max_c": 60.0,
     "pass_min_minutes": 18, "pass_min_capacity_pct": 90,
     "is_active": True},
    {"id": 4, "part_number": "3214-31", "amendment": "A",
     "description": "DIEHL NiCd 6V 4Ah EPSU Battery (Original)",
     "manufacturer": "DIEHL Aerospace GmbH", "manufacturer_code": "D1347",
     "nominal_voltage_v": 6.0, "capacity_ah": 4.0, "num_cells": 5, "chemistry": "NiCd",
     "std_charge_current_ma": 400, "std_charge_duration_h": 16.0,
     "std_charge_voltage_limit_mv": 8900, "cap_test_current_a": 0.8,
     "cap_test_voltage_min_mv": 5000, "cap_test_duration_min": 480,
     "pre_discharge_current_a": 0.8, "pre_discharge_end_voltage_mv": 5000,
     "post_charge_current_ma": 400, "post_charge_duration_h": 16.0,
     "rest_before_cap_test_min": 240,
     "fast_discharge_enabled": False,
     "max_temp_c": 45.0, "discharge_max_temp_c": 50.0, "emergency_temp_max_c": 55.0,
     "pass_min_minutes": 270, "pass_min_capacity_pct": 80,
     "is_active": True},
    {"id": 5, "part_number": "3214-31", "amendment": "B",
     "description": "DIEHL NiCd 6V 4Ah EPSU Battery",
     "manufacturer": "DIEHL Aerospace GmbH", "manufacturer_code": "D1347",
     "nominal_voltage_v": 6.0, "capacity_ah": 4.0, "num_cells": 5, "chemistry": "NiCd",
     "std_charge_current_ma": 400, "std_charge_duration_h": 16.0,
     "std_charge_voltage_limit_mv": 9000, "cap_test_current_a": 0.8,
     "cap_test_voltage_min_mv": 5000, "cap_test_duration_min": 480,
     "pre_discharge_current_a": 0.8, "pre_discharge_end_voltage_mv": 5000,
     "post_charge_current_ma": 400, "post_charge_duration_h": 16.0,
     "rest_before_cap_test_min": 240,
     "fast_discharge_enabled": False,
     "max_temp_c": 45.0, "discharge_max_temp_c": 55.0, "emergency_temp_max_c": 60.0,
     "pass_min_minutes": 270, "pass_min_capacity_pct": 85,
     "is_active": True},
    {"id": 6, "part_number": "301-3017", "amendment": "",
     "description": "Cobham NiCd 6V 2.3Ah EPSU Battery (Original)",
     "manufacturer": "Cobham Mission Systems", "manufacturer_code": "F6175",
     "nominal_voltage_v": 6.0, "capacity_ah": 2.3, "num_cells": 5, "chemistry": "NiCd",
     "std_charge_current_ma": 230, "std_charge_duration_h": 16.0,
     "std_charge_voltage_limit_mv": 9000, "cap_test_current_a": 0.46,
     "cap_test_voltage_min_mv": 5000, "cap_test_duration_min": 480,
     "pre_discharge_current_a": 0.46, "pre_discharge_end_voltage_mv": 5000,
     "post_charge_current_ma": 230, "post_charge_duration_h": 16.0,
     "rest_before_cap_test_min": 60,
     "fast_discharge_enabled": True, "fast_discharge_current_a": 4.0,
     "fast_discharge_end_voltage_mv": 5000, "fast_discharge_duration_min": 60,
     "max_temp_c": 45.0, "discharge_max_temp_c": 55.0, "emergency_temp_max_c": 60.0,
     "pass_min_minutes": 270, "pass_min_capacity_pct": 85,
     "is_active": True},
    {"id": 7, "part_number": "301-3017", "amendment": "A",
     "description": "Cobham NiCd 6V 2.3Ah EPSU Battery (Rev 2023)",
     "manufacturer": "Cobham Mission Systems", "manufacturer_code": "F6175",
     "nominal_voltage_v": 6.0, "capacity_ah": 2.3, "num_cells": 5, "chemistry": "NiCd",
     "std_charge_current_ma": 230, "std_charge_duration_h": 14.0,
     "std_charge_voltage_limit_mv": 9100, "cap_test_current_a": 0.46,
     "cap_test_voltage_min_mv": 5100, "cap_test_duration_min": 450,
     "pre_discharge_current_a": 0.46, "pre_discharge_end_voltage_mv": 5100,
     "post_charge_current_ma": 230, "post_charge_duration_h": 14.0,
     "rest_before_cap_test_min": 60,
     "fast_discharge_enabled": True, "fast_discharge_current_a": 4.6,
     "fast_discharge_end_voltage_mv": 5100, "fast_discharge_duration_min": 55,
     "max_temp_c": 45.0, "discharge_max_temp_c": 55.0, "emergency_temp_max_c": 60.0,
     "pass_min_minutes": 260, "pass_min_capacity_pct": 85,
     "is_active": True},
]


# =============================================================================
# RECIPES (8 records)
# =============================================================================

SEED_RECIPES = [
    # --- CMM 33-51-01 (3301-31) ---
    {"id": 1, "tech_pub_id": 1, "cmm_reference": "Section 3.2",
     "name": "Capacity Test", "description": "Full capacity test per CMM 33-51-01 Section 3.2",
     "recipe_type": "capacity_test", "is_default": True,
     "applicable_part_numbers": ["3301-31"],
     "steps": [
         {"step_number": 1, "step_type": "discharge", "label": "Pre-Discharge",
          "description": "Discharge to end voltage", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 2, "step_type": "rest", "label": "Pre-Discharge Rest",
          "description": "Cool-down rest period", "param_source": "fixed", "param_overrides": {"duration_min": 60}},
         {"step_number": 3, "step_type": "charge", "label": "Standard Charge",
          "description": "Charge per EEPROM parameters", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 4, "step_type": "rest", "label": "Post-Charge Rest",
          "description": "Rest before capacity discharge", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 5, "step_type": "discharge", "label": "Capacity Discharge",
          "description": "Timed capacity discharge to end voltage", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 6, "step_type": "charge", "label": "Post-Test Charge",
          "description": "Return charge after test", "param_source": "eeprom", "param_overrides": {}},
     ], "is_active": True},
    {"id": 2, "tech_pub_id": 1, "cmm_reference": "Section 3.1",
     "name": "Charge Only", "description": "Standard charge per CMM 33-51-01 Section 3.1",
     "recipe_type": "charge_only", "is_default": False,
     "applicable_part_numbers": ["3301-31"],
     "steps": [
         {"step_number": 1, "step_type": "discharge", "label": "Pre-Discharge",
          "description": "Discharge before charge", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 2, "step_type": "rest", "label": "Rest",
          "description": "Cool-down rest", "param_source": "fixed", "param_overrides": {"duration_min": 60}},
         {"step_number": 3, "step_type": "charge", "label": "Standard Charge",
          "description": "Charge per EEPROM parameters", "param_source": "eeprom", "param_overrides": {}},
     ], "is_active": True},
    {"id": 3, "tech_pub_id": 1, "cmm_reference": "Section 3.3",
     "name": "Reconditioning", "description": "Full reconditioning cycle per CMM 33-51-01 Section 3.3",
     "recipe_type": "reconditioning", "is_default": False,
     "applicable_part_numbers": ["3301-31"],
     "steps": [
         {"step_number": 1, "step_type": "discharge", "label": "Initial Discharge",
          "description": "Deep discharge to end voltage", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 2, "step_type": "rest", "label": "Rest 1",
          "description": "Cool-down rest", "param_source": "fixed", "param_overrides": {"duration_min": 60}},
         {"step_number": 3, "step_type": "charge", "label": "Reconditioning Charge 1",
          "description": "First reconditioning charge", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 4, "step_type": "rest", "label": "Rest 2",
          "description": "Intermediate rest", "param_source": "fixed", "param_overrides": {"duration_min": 60}},
         {"step_number": 5, "step_type": "discharge", "label": "Reconditioning Discharge",
          "description": "Second discharge cycle", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 6, "step_type": "rest", "label": "Rest 3",
          "description": "Cool-down rest", "param_source": "fixed", "param_overrides": {"duration_min": 60}},
         {"step_number": 7, "step_type": "charge", "label": "Reconditioning Charge 2",
          "description": "Second reconditioning charge", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 8, "step_type": "rest", "label": "Post-Charge Rest",
          "description": "Rest before verification discharge", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 9, "step_type": "discharge", "label": "Verification Discharge",
          "description": "Capacity verification discharge", "param_source": "eeprom", "param_overrides": {}},
     ], "is_active": True},

    # --- CMM 33-51-17 (3214-31) ---
    {"id": 4, "tech_pub_id": 2, "cmm_reference": "Section 3.2",
     "name": "Capacity Test", "description": "Full capacity test per CMM 33-51-17 Section 3.2",
     "recipe_type": "capacity_test", "is_default": True,
     "applicable_part_numbers": ["3214-31"],
     "steps": [
         {"step_number": 1, "step_type": "discharge", "label": "Pre-Discharge",
          "description": "Discharge to end voltage", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 2, "step_type": "rest", "label": "Pre-Discharge Rest",
          "description": "Cool-down rest period", "param_source": "fixed", "param_overrides": {"duration_min": 60}},
         {"step_number": 3, "step_type": "charge", "label": "Standard Charge",
          "description": "Charge per EEPROM parameters", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 4, "step_type": "rest", "label": "Post-Charge Rest",
          "description": "Rest before capacity discharge", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 5, "step_type": "discharge", "label": "Capacity Discharge",
          "description": "Timed capacity discharge to end voltage", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 6, "step_type": "charge", "label": "Post-Test Charge",
          "description": "Return charge after test", "param_source": "eeprom", "param_overrides": {}},
     ], "is_active": True},
    {"id": 5, "tech_pub_id": 2, "cmm_reference": "Section 3.1",
     "name": "Charge Only", "description": "Standard charge per CMM 33-51-17 Section 3.1",
     "recipe_type": "charge_only", "is_default": False,
     "applicable_part_numbers": ["3214-31"],
     "steps": [
         {"step_number": 1, "step_type": "discharge", "label": "Pre-Discharge",
          "description": "Discharge before charge", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 2, "step_type": "rest", "label": "Rest",
          "description": "Cool-down rest", "param_source": "fixed", "param_overrides": {"duration_min": 60}},
         {"step_number": 3, "step_type": "charge", "label": "Standard Charge",
          "description": "Charge per EEPROM parameters", "param_source": "eeprom", "param_overrides": {}},
     ], "is_active": True},

    # --- CMM 33-51-22 (301-3017) ---
    {"id": 6, "tech_pub_id": 3, "cmm_reference": "Section 3.2",
     "name": "Capacity Test", "description": "Full capacity test per CMM 33-51-22 Section 3.2",
     "recipe_type": "capacity_test", "is_default": True,
     "applicable_part_numbers": ["301-3017"],
     "steps": [
         {"step_number": 1, "step_type": "discharge", "label": "Pre-Discharge",
          "description": "Discharge to end voltage", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 2, "step_type": "rest", "label": "Pre-Discharge Rest",
          "description": "Cool-down rest period", "param_source": "fixed", "param_overrides": {"duration_min": 60}},
         {"step_number": 3, "step_type": "charge", "label": "Standard Charge",
          "description": "Charge per EEPROM parameters", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 4, "step_type": "rest", "label": "Post-Charge Rest",
          "description": "Rest before capacity discharge", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 5, "step_type": "discharge", "label": "Capacity Discharge",
          "description": "Timed capacity discharge to end voltage", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 6, "step_type": "charge", "label": "Post-Test Charge",
          "description": "Return charge after test", "param_source": "eeprom", "param_overrides": {}},
     ], "is_active": True},
    {"id": 7, "tech_pub_id": 3, "cmm_reference": "Section 3.1",
     "name": "Charge Only", "description": "Standard charge per CMM 33-51-22 Section 3.1",
     "recipe_type": "charge_only", "is_default": False,
     "applicable_part_numbers": ["301-3017"],
     "steps": [
         {"step_number": 1, "step_type": "discharge", "label": "Pre-Discharge",
          "description": "Discharge before charge", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 2, "step_type": "rest", "label": "Rest",
          "description": "Cool-down rest", "param_source": "fixed", "param_overrides": {"duration_min": 60}},
         {"step_number": 3, "step_type": "charge", "label": "Standard Charge",
          "description": "Charge per EEPROM parameters", "param_source": "eeprom", "param_overrides": {}},
     ], "is_active": True},
    {"id": 8, "tech_pub_id": 3, "cmm_reference": "Section 3.4",
     "name": "Fast Discharge Test", "description": "Fast discharge capacity test per CMM 33-51-22 Section 3.4",
     "recipe_type": "fast_discharge", "is_default": False,
     "applicable_part_numbers": ["301-3017"],
     "steps": [
         {"step_number": 1, "step_type": "discharge", "label": "Pre-Discharge",
          "description": "Discharge to end voltage", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 2, "step_type": "rest", "label": "Pre-Discharge Rest",
          "description": "Cool-down rest period", "param_source": "fixed", "param_overrides": {"duration_min": 60}},
         {"step_number": 3, "step_type": "charge", "label": "Standard Charge",
          "description": "Charge per EEPROM parameters", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 4, "step_type": "rest", "label": "Post-Charge Rest",
          "description": "Rest before fast discharge", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 5, "step_type": "discharge", "label": "Fast Discharge",
          "description": "High-rate discharge test", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 6, "step_type": "rest", "label": "Post-Discharge Rest",
          "description": "Cool-down after fast discharge", "param_source": "fixed", "param_overrides": {"duration_min": 60}},
         {"step_number": 7, "step_type": "charge", "label": "Recovery Charge",
          "description": "Recovery charge after fast discharge", "param_source": "eeprom", "param_overrides": {}},
         {"step_number": 8, "step_type": "charge", "label": "Post-Test Charge",
          "description": "Final return charge", "param_source": "eeprom", "param_overrides": {}},
     ], "is_active": True},
]


# =============================================================================
# CALIBRATED TOOLS (6 records)
# =============================================================================

SEED_TOOLS = [
    {"id": 1, "part_number": "Fluke-87V", "description": "Fluke 87V Digital Multimeter",
     "manufacturer": "Fluke Corporation", "serial_number": "FL-2024-0042",
     "calibration_date": "2025-08-15", "valid_until": "2026-08-15",
     "internal_reference": "OT-CAL-0012", "category": "multimeter", "is_active": True,
     "calibration_certificate": "CERT-2025-FL0042-A", "calibrated_by": "Trescal GmbH"},
    {"id": 2, "part_number": "Fluke-87V", "description": "Fluke 87V Digital Multimeter",
     "manufacturer": "Fluke Corporation", "serial_number": "FL-2024-0043",
     "calibration_date": "2025-03-10", "valid_until": "2026-03-10",
     "internal_reference": "OT-CAL-0013", "category": "multimeter", "is_active": True,
     "calibration_certificate": "CERT-2025-FL0043-A", "calibrated_by": "Trescal GmbH"},
    {"id": 3, "part_number": "Fluke-1507", "description": "Fluke 1507 Insulation Tester",
     "manufacturer": "Fluke Corporation", "serial_number": "FL-2023-1100",
     "calibration_date": "2025-11-20", "valid_until": "2026-11-20",
     "internal_reference": "OT-CAL-0020", "category": "insulation_tester", "is_active": True,
     "calibration_certificate": "CERT-2025-FL1100-B", "calibrated_by": "Aerolab Calibration Services"},
    {"id": 4, "part_number": "CDI-2502MRMH", "description": "CDI Torque Wrench 3/8 Drive 10-250 in-lb",
     "manufacturer": "CDI Torque Products", "serial_number": "CDI-2022-0087",
     "calibration_date": "2025-06-01", "valid_until": "2026-06-01",
     "internal_reference": "OT-CAL-0031", "category": "torque_wrench", "is_active": True,
     "calibration_certificate": "CERT-2025-CDI087-A", "calibrated_by": "Trescal GmbH"},
    {"id": 5, "part_number": "Fluke-52-II", "description": "Fluke 52 II Dual Input Thermometer",
     "manufacturer": "Fluke Corporation", "serial_number": "FL-2024-0500",
     "calibration_date": "2025-09-01", "valid_until": "2026-09-01",
     "internal_reference": "OT-CAL-0045", "category": "thermometer", "is_active": True,
     "calibration_certificate": "CERT-2025-FL0500-A", "calibrated_by": "Aerolab Calibration Services"},
    {"id": 6, "part_number": "Fluke-87V", "description": "Fluke 87V Digital Multimeter (EXPIRED)",
     "manufacturer": "Fluke Corporation", "serial_number": "FL-2020-0010",
     "calibration_date": "2024-06-15", "valid_until": "2025-06-15",
     "internal_reference": "OT-CAL-0005", "category": "multimeter", "is_active": True,
     "calibration_certificate": "CERT-2024-FL0010-C", "calibrated_by": "Trescal GmbH"},
]


# =============================================================================
# STATION CALIBRATIONS (24 records — 12 stations x 2 units each)
# =============================================================================

# PSU verification test points (abbreviated reference — full definition in mock_server.py)
# 14 voltage accuracy points (0.1V to 16V) + 6 regulation points (7.2V at 0.5A to 8A)
_PSU_VOLTAGE_POINTS = [0.1, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 9.0, 10.0, 12.0, 14.0, 15.5, 16.0]
_PSU_REGULATION_CURRENTS = [0.5, 1.0, 2.0, 4.0, 6.0, 8.0]

# DC Load verification test points (abbreviated reference — full definition in mock_server.py)
# 10 current sink points (0.01A to 5A) + 10 voltage readback points (0.5V to 16V)
_LOAD_CURRENT_POINTS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
_LOAD_VOLTAGE_POINTS = [0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0]


def _build_station_calibrations():
    """Generate station calibration records with 20-point verification readings."""
    import random
    random.seed(42)  # Deterministic seed data
    rows = []
    for sid in range(1, 13):
        if sid <= 6:
            cal_date = f"2025-{8 + (sid % 4):02d}-{10 + sid:02d}"
            next_due = f"2026-{8 + (sid % 4):02d}-{10 + sid:02d}"
            psu_result = "pass"
            load_result = "pass"
        elif sid <= 9:
            cal_date = f"2025-03-{10 + sid:02d}"
            next_due = f"2026-03-{10 + sid:02d}"
            psu_result = "pass"
            load_result = "pass"
        elif sid == 10:
            cal_date = "2025-07-15"
            next_due = "2026-07-15"
            psu_result = "fail"
            load_result = "pass"
        else:
            cal_date = None
            next_due = None
            psu_result = None
            load_result = None

        # PSU readings: 14 voltage + 6 regulation = 20 points
        psu_readings = []
        if cal_date:
            step = 0
            for v in _PSU_VOLTAGE_POINTS:
                step += 1
                drift = random.uniform(-0.004, 0.004) if psu_result == "pass" else 0.15
                measured = round(v + drift, 4)
                tol = round(v * 0.0005 + 0.010, 4)  # ±(0.05% + 10mV)
                psu_readings.append({
                    "step": step,
                    "set_value": f"{v:.3f} V / 0.1 A",
                    "measured_value": f"{measured:.4f} V",
                    "tolerance": f"\u00b1{tol:.4f} V",
                    "pass": abs(measured - v) <= tol,
                })
            for a in _PSU_REGULATION_CURRENTS:
                step += 1
                drift = random.uniform(-0.004, 0.004) if psu_result == "pass" else 0.15
                measured = round(7.2 + drift, 4)
                tol = round(7.2 * 0.0005 + 0.010, 4)
                psu_readings.append({
                    "step": step,
                    "set_value": f"7.200 V / {a:.3f} A",
                    "measured_value": f"{measured:.4f} V",
                    "tolerance": f"\u00b1{tol:.4f} V",
                    "pass": abs(measured - 7.2) <= tol,
                })
        rows.append({
            "station_id": sid,
            "unit": "psu",
            "model": "SPD1168X" if sid <= 6 else "SPD1168X",
            "serial_number": f"SPD1XDAD{sid:02d}R{2024 + (sid // 7):04d}",
            "last_calibration_date": cal_date,
            "next_due_date": next_due,
            "calibrated_by": "Orion Technik (in-house)" if cal_date else None,
            "calibration_certificate": f"INT-PSU-{sid:02d}-2025" if cal_date else None,
            "result": psu_result,
            "readings": psu_readings,
        })

        # DC Load readings: 10 current + 10 voltage = 20 points
        load_readings = []
        if cal_date:
            step = 0
            for a in _LOAD_CURRENT_POINTS:
                step += 1
                drift = random.uniform(-0.001, 0.001)
                measured = round(a + drift, 4)
                tol = round(a * 0.0003 + 0.0025, 4)  # ±(0.03% + 2.5mA)
                load_readings.append({
                    "step": step,
                    "set_value": f"{a:.3f} A CC",
                    "measured_value": f"{measured:.4f} A",
                    "tolerance": f"\u00b1{tol:.4f} A",
                    "pass": abs(measured - a) <= tol,
                })
            for v in _LOAD_VOLTAGE_POINTS:
                step += 1
                drift = random.uniform(-0.003, 0.003)
                measured = round(v + drift, 4)
                tol = round(v * 0.00015 + 0.0072, 4)  # ±(0.015% + 7.2mV)
                load_readings.append({
                    "step": step,
                    "set_value": f"{v:.3f} V readback",
                    "measured_value": f"{measured:.4f} V",
                    "tolerance": f"\u00b1{tol:.4f} V",
                    "pass": abs(measured - v) <= tol,
                })
        rows.append({
            "station_id": sid,
            "unit": "dc_load",
            "model": "SDL1030X" if sid <= 6 else "SDL1030X",
            "serial_number": f"SDL1X{sid:02d}R{2024 + (sid // 7):04d}",
            "last_calibration_date": cal_date,
            "next_due_date": next_due,
            "calibrated_by": "Orion Technik (in-house)" if cal_date else None,
            "calibration_certificate": f"INT-LOAD-{sid:02d}-2025" if cal_date else None,
            "result": load_result,
            "readings": load_readings,
        })
    return rows


SEED_STATION_CALIBRATIONS = _build_station_calibrations()


# =============================================================================
# WORK ORDERS (5 records) — items extracted to SEED_WORK_ORDER_ITEMS
# =============================================================================

SEED_WORK_ORDERS = [
    {"id": 1, "work_order_number": "OT-2026-0001", "customer_reference": "TAP-BAT-2026-42",
     "customer_id": 1,
     "service_type": "capacity_test", "priority": "normal",
     "status": "in_progress", "received_date": "2026-02-10T10:00:00",
     "assigned_technician": "Angelo",
     "customer_notes": "Routine capacity test, 8 batteries from A320 fleet"},
    {"id": 2, "work_order_number": "OT-2026-0002", "customer_reference": "SATA-SVC-0088",
     "customer_id": 2,
     "service_type": "full_service", "priority": "urgent",
     "status": "received", "received_date": "2026-02-14T09:30:00",
     "assigned_technician": "",
     "customer_notes": "Battery low capacity reported by crew, urgent turnaround needed"},
    {"id": 3, "work_order_number": "OT-2026-0003", "customer_reference": "",
     "customer_id": 3,
     "service_type": "reconditioning", "priority": "normal",
     "status": "received", "received_date": "2026-02-15T14:00:00",
     "assigned_technician": "",
     "customer_notes": "12 batteries in storage for >8 months, need reconditioning before return to service"},
    {"id": 4, "work_order_number": "OT-2026-0004", "customer_reference": "PGA-MX-2026-11",
     "customer_id": 4,
     "service_type": "capacity_test", "priority": "normal",
     "status": "completed", "received_date": "2026-02-05T11:00:00",
     "completed_date": "2026-02-12T17:00:00",
     "assigned_technician": "Angelo",
     "customer_notes": "Scheduled maintenance batch"},
    {"id": 5, "work_order_number": "OT-2026-0005", "customer_reference": "TAP-BAT-2026-55",
     "customer_id": 1,
     "service_type": "charge_only", "priority": "low",
     "status": "received", "received_date": "2026-02-16T08:00:00",
     "assigned_technician": "",
     "customer_notes": "Charge only for delivery batteries, no cap test needed"},
]

SEED_WORK_ORDER_ITEMS = [
    # --- WO 1 (TAP Air Portugal, 8 items) ---
    {"id": 1, "work_order_id": 1, "serial_number": "D1347-2024-0042",
     "part_number": "3301-31", "revision": "A", "amendment": "A",
     "reported_condition": "Normal", "status": "testing"},
    {"id": 2, "work_order_id": 1, "serial_number": "D1347-2024-0043",
     "part_number": "3301-31", "revision": "A", "amendment": "A",
     "reported_condition": "Normal", "status": "testing"},
    {"id": 3, "work_order_id": 1, "serial_number": "D1347-2024-0044",
     "part_number": "3301-31", "revision": "A", "amendment": "A",
     "reported_condition": "Low capacity reported", "status": "queued"},
    {"id": 4, "work_order_id": 1, "serial_number": "D1347-2024-0045",
     "part_number": "3301-31", "revision": "A", "amendment": "A",
     "reported_condition": "Normal", "status": "queued"},
    {"id": 5, "work_order_id": 1, "serial_number": "D1347-2023-0198",
     "part_number": "3301-31", "revision": "A", "amendment": "A",
     "reported_condition": "Normal", "status": "completed"},
    {"id": 6, "work_order_id": 1, "serial_number": "D1347-2023-0199",
     "part_number": "3301-31", "revision": "A", "amendment": "A",
     "reported_condition": "Corrosion on terminals", "status": "completed"},
    {"id": 7, "work_order_id": 1, "serial_number": "D1347-2024-0046",
     "part_number": "3301-31", "revision": "A", "amendment": "A",
     "reported_condition": "Normal", "status": "queued"},
    {"id": 8, "work_order_id": 1, "serial_number": "D1347-2024-0047",
     "part_number": "3301-31", "revision": "A", "amendment": "A",
     "reported_condition": "Normal", "status": "queued"},
    # --- WO 2 (SATA Air Azores, 3 items) ---
    {"id": 9, "work_order_id": 2, "serial_number": "F6175-2023-0118",
     "part_number": "301-3017", "revision": "C", "amendment": "",
     "reported_condition": "Low capacity, crew report", "status": "queued"},
    {"id": 10, "work_order_id": 2, "serial_number": "F6175-2023-0119",
     "part_number": "301-3017", "revision": "C", "amendment": "",
     "reported_condition": "Normal", "status": "queued"},
    {"id": 11, "work_order_id": 2, "serial_number": "F6175-2022-0087",
     "part_number": "301-3017", "revision": "B", "amendment": "",
     "reported_condition": "In storage >6 months", "status": "queued"},
    # --- WO 3 (Ryanair, 4 items) ---
    {"id": 12, "work_order_id": 3, "serial_number": "D1347-2022-0391",
     "part_number": "3214-31", "revision": "B", "amendment": "B",
     "reported_condition": "Long storage", "status": "queued"},
    {"id": 13, "work_order_id": 3, "serial_number": "D1347-2022-0392",
     "part_number": "3214-31", "revision": "B", "amendment": "B",
     "reported_condition": "Long storage", "status": "queued"},
    {"id": 14, "work_order_id": 3, "serial_number": "D1347-2022-0393",
     "part_number": "3214-31", "revision": "B", "amendment": "B",
     "reported_condition": "Long storage", "status": "queued"},
    {"id": 15, "work_order_id": 3, "serial_number": "D1347-2022-0394",
     "part_number": "3214-31", "revision": "B", "amendment": "B",
     "reported_condition": "Long storage", "status": "queued"},
    # --- WO 4 (Portugalia Airlines, 2 items) ---
    {"id": 16, "work_order_id": 4, "serial_number": "D1347-2024-0100",
     "part_number": "3301-31", "revision": "A", "amendment": "A",
     "reported_condition": "Normal", "status": "completed"},
    {"id": 17, "work_order_id": 4, "serial_number": "D1347-2024-0101",
     "part_number": "3301-31", "revision": "A", "amendment": "A",
     "reported_condition": "Normal", "status": "completed"},
    # --- WO 5 (TAP Air Portugal, 6 items) ---
    {"id": 18, "work_order_id": 5, "serial_number": "D1347-2025-0001",
     "part_number": "3214-31", "revision": "B", "amendment": "B",
     "reported_condition": "New from factory", "status": "queued"},
    {"id": 19, "work_order_id": 5, "serial_number": "D1347-2025-0002",
     "part_number": "3214-31", "revision": "B", "amendment": "B",
     "reported_condition": "New from factory", "status": "queued"},
    {"id": 20, "work_order_id": 5, "serial_number": "D1347-2025-0003",
     "part_number": "3214-31", "revision": "B", "amendment": "B",
     "reported_condition": "New from factory", "status": "queued"},
    {"id": 21, "work_order_id": 5, "serial_number": "D1347-2025-0004",
     "part_number": "3214-31", "revision": "B", "amendment": "B",
     "reported_condition": "New from factory", "status": "queued"},
    {"id": 22, "work_order_id": 5, "serial_number": "D1347-2025-0005",
     "part_number": "3214-31", "revision": "B", "amendment": "B",
     "reported_condition": "New from factory", "status": "queued"},
    {"id": 23, "work_order_id": 5, "serial_number": "D1347-2025-0006",
     "part_number": "3214-31", "revision": "B", "amendment": "B",
     "reported_condition": "New from factory", "status": "queued"},
]


# =============================================================================
# WORK JOBS (3 records) — tasks extracted to SEED_WORK_JOB_TASKS
# =============================================================================

SEED_WORK_JOBS = [
    {"id": 1, "work_order_id": 1, "work_order_item_id": 1,
     "work_order_number": "OT-2026-0001",
     "battery_serial": "D1347-2024-0042", "battery_part_number": "3301-31", "battery_amendment": "A",
     "tech_pub_id": 1, "tech_pub_cmm": "33-51-01", "tech_pub_revision": "Original",
     "recipe_id": 1, "recipe_name": "Capacity Test", "recipe_cmm_ref": "Section 3.2",
     "station_id": 1, "status": "in_progress",
     "started_at": "2026-02-16T08:00:00", "completed_at": None,
     "started_by": "Angelo", "result": None,
     "created_at": "2026-02-16T08:00:00"},
    {"id": 2, "work_order_id": 1, "work_order_item_id": 2,
     "work_order_number": "OT-2026-0001",
     "battery_serial": "D1347-2024-0043", "battery_part_number": "3301-31", "battery_amendment": "A",
     "tech_pub_id": 1, "tech_pub_cmm": "33-51-01", "tech_pub_revision": "Original",
     "recipe_id": 1, "recipe_name": "Capacity Test", "recipe_cmm_ref": "Section 3.2",
     "station_id": 2, "status": "in_progress",
     "started_at": "2026-02-16T07:30:00", "completed_at": None,
     "started_by": "Angelo", "result": None,
     "created_at": "2026-02-16T07:30:00"},
    {"id": 3, "work_order_id": 2, "work_order_item_id": 9,
     "work_order_number": "OT-2026-0002",
     "battery_serial": "F6175-2023-0118", "battery_part_number": "301-3017", "battery_amendment": "",
     "tech_pub_id": 3, "tech_pub_cmm": "33-51-22", "tech_pub_revision": "Revision 12",
     "recipe_id": 6, "recipe_name": "Capacity Test", "recipe_cmm_ref": "Section 3.2",
     "station_id": 5, "status": "completed",
     "started_at": "2026-02-15T08:00:00", "completed_at": "2026-02-15T18:45:00",
     "started_by": "Angelo", "result": "pass",
     "created_at": "2026-02-15T08:00:00"},
]

SEED_WORK_JOB_TASKS = [
    # --- Job 1 tasks (2 completed tasks) ---
    {"id": 1, "work_job_id": 1, "task_number": 1, "step_number": 1,
     "type": "discharge", "label": "Pre-Discharge",
     "params": {"current_ma": 5000, "voltage_min_mv": 5000, "duration_min": 60},
     "source": "recipe", "tools_used": [],
     "measured_values": {},
     "start_time": "2026-02-16T08:00:00", "end_time": "2026-02-16T08:28:00",
     "chart_data": [], "data_points": 1680, "status": "completed", "result_notes": ""},
    {"id": 2, "work_job_id": 1, "task_number": 2, "step_number": 2,
     "type": "rest", "label": "Pre-Discharge Rest",
     "params": {"duration_min": 60},
     "source": "recipe", "tools_used": [],
     "measured_values": {},
     "start_time": "2026-02-16T08:28:00", "end_time": "2026-02-16T09:28:00",
     "chart_data": [], "data_points": 3600, "status": "completed", "result_notes": ""},
    # --- Job 3 tasks (6 completed tasks — full capacity test) ---
    {"id": 3, "work_job_id": 3, "task_number": 1, "step_number": 1,
     "type": "discharge", "label": "Pre-Discharge",
     "params": {"current_ma": 460, "voltage_min_mv": 5000, "duration_min": 480},
     "source": "recipe",
     "tools_used": [
         {"tool_id": 1, "internal_reference": "OT-CAL-0012", "valid_until": "2026-08-15",
          "description": "Fluke 87V Digital Multimeter",
          "calibration_certificate": "CERT-2025-FL0042-A"}],
     "measured_values": {"voltage_start_mv": 6350, "voltage_end_mv": 5010,
                         "current_ma": 462, "temperature_c": 28.3},
     "step_result": "pass",
     "start_time": "2026-02-15T08:00:00", "end_time": "2026-02-15T08:42:00",
     "chart_data": [{"t": i * 10, "V": round(6350 - i * 32, 1), "I": 462,
                     "T": round(25.0 + i * 0.08, 1)} for i in range(252)],
     "data_points": 252, "status": "completed",
     "result_notes": "Discharged to 5010 mV in 42 min"},
    {"id": 4, "work_job_id": 3, "task_number": 2, "step_number": 2,
     "type": "rest", "label": "Pre-Discharge Rest",
     "params": {"duration_min": 60},
     "source": "recipe", "tools_used": [],
     "measured_values": {"voltage_start_mv": 5010, "voltage_end_mv": 5280,
                         "temperature_c": 26.1},
     "step_result": "pass",
     "start_time": "2026-02-15T08:42:00", "end_time": "2026-02-15T09:42:00",
     "chart_data": [{"t": i * 10, "V": round(5010 + i * 0.75, 1), "I": 0,
                     "T": round(28.3 - i * 0.006, 1)} for i in range(360)],
     "data_points": 360, "status": "completed", "result_notes": ""},
    {"id": 5, "work_job_id": 3, "task_number": 3, "step_number": 3,
     "type": "charge", "label": "Standard Charge",
     "params": {"current_ma": 230, "voltage_mv": 9000, "duration_min": 960},
     "source": "recipe",
     "tools_used": [
         {"tool_id": 1, "internal_reference": "OT-CAL-0012", "valid_until": "2026-08-15",
          "description": "Fluke 87V Digital Multimeter",
          "calibration_certificate": "CERT-2025-FL0042-A"},
         {"tool_id": 5, "internal_reference": "OT-CAL-0045", "valid_until": "2026-09-01",
          "description": "Fluke 52 II Dual Input Thermometer",
          "calibration_certificate": "CERT-2025-FL0500-A"}],
     "measured_values": {"voltage_start_mv": 5280, "voltage_end_mv": 8420,
                         "current_ma": 231, "temperature_c": 33.5},
     "step_result": "pass",
     "start_time": "2026-02-15T09:42:00", "end_time": "2026-02-15T13:42:00",
     "chart_data": [{"t": i * 10, "V": round(5280 + i * 2.183, 1), "I": 231,
                     "T": round(26.0 + i * 0.00517, 1)} for i in range(1440)],
     "data_points": 1440, "status": "completed",
     "result_notes": "Charged to 8420 mV"},
    {"id": 6, "work_job_id": 3, "task_number": 4, "step_number": 4,
     "type": "rest", "label": "Post-Charge Rest",
     "params": {"duration_min": 60},
     "source": "recipe", "tools_used": [],
     "measured_values": {"voltage_start_mv": 8420, "voltage_end_mv": 7650,
                         "temperature_c": 29.8},
     "step_result": "pass",
     "start_time": "2026-02-15T13:42:00", "end_time": "2026-02-15T14:42:00",
     "chart_data": [{"t": i * 10, "V": round(8420 - i * 2.14, 1), "I": 0,
                     "T": round(33.5 - i * 0.01, 1)} for i in range(360)],
     "data_points": 360, "status": "completed", "result_notes": ""},
    {"id": 7, "work_job_id": 3, "task_number": 5, "step_number": 5,
     "type": "discharge", "label": "Capacity Discharge",
     "params": {"current_ma": 460, "voltage_min_mv": 5000, "duration_min": 480},
     "source": "recipe",
     "tools_used": [
         {"tool_id": 1, "internal_reference": "OT-CAL-0012", "valid_until": "2026-08-15",
          "description": "Fluke 87V Digital Multimeter",
          "calibration_certificate": "CERT-2025-FL0042-A"},
         {"tool_id": 5, "internal_reference": "OT-CAL-0045", "valid_until": "2026-09-01",
          "description": "Fluke 52 II Dual Input Thermometer",
          "calibration_certificate": "CERT-2025-FL0500-A"}],
     "measured_values": {"voltage_start_mv": 7650, "voltage_end_mv": 5000,
                         "current_ma": 461, "temperature_c": 34.2,
                         "discharge_time_min": 298, "capacity_pct": 97.1},
     "step_result": "pass",
     "start_time": "2026-02-15T14:42:00", "end_time": "2026-02-15T19:40:00",
     "chart_data": [{"t": i * 10, "V": round(7650 - i * 1.475, 1), "I": 461,
                     "T": round(29.8 + i * 0.0025, 1)} for i in range(1788)],
     "data_points": 1788, "status": "completed",
     "result_notes": "Capacity: 298 min (97.1%) \u2014 PASS (min 270 min / 85%)"},
    {"id": 8, "work_job_id": 3, "task_number": 6, "step_number": 6,
     "type": "charge", "label": "Post-Test Charge",
     "params": {"current_ma": 230, "voltage_mv": 9000, "duration_min": 960},
     "source": "recipe",
     "tools_used": [
         {"tool_id": 1, "internal_reference": "OT-CAL-0012", "valid_until": "2026-08-15",
          "description": "Fluke 87V Digital Multimeter",
          "calibration_certificate": "CERT-2025-FL0042-A"}],
     "measured_values": {"voltage_start_mv": 5000, "voltage_end_mv": 8380,
                         "current_ma": 230, "temperature_c": 32.1},
     "step_result": "pass",
     "start_time": "2026-02-15T19:40:00", "end_time": "2026-02-15T23:40:00",
     "chart_data": [{"t": i * 10, "V": round(5000 + i * 2.35, 1), "I": 230,
                     "T": round(28.0 + i * 0.00283, 1)} for i in range(1440)],
     "data_points": 1440, "status": "completed",
     "result_notes": "Return charge complete"},
]


# =============================================================================
# TECH PUB APPLICABILITY (from existing JSON applicable_part_numbers)
# =============================================================================

SEED_TECH_PUB_APPLICABILITY = [
    {"tech_pub_id": 1, "part_number": "3301-31", "amendment": ""},
    {"tech_pub_id": 2, "part_number": "3214-31", "amendment": ""},
    {"tech_pub_id": 3, "part_number": "301-3017", "amendment": ""},
]


# =============================================================================
# TECH PUB SECTIONS (ordered CMM sections for each tech pub)
# =============================================================================

SEED_TECH_PUB_SECTIONS = [
    # --- CMM 33-51-01 (3301-31) ---
    {"id": 1, "tech_pub_id": 1, "section_number": "3.1", "title": "Visual Inspection",
     "section_type": "inspection", "sort_order": 10, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 2, "tech_pub_id": 1, "section_number": "3.2", "title": "Weight Check",
     "section_type": "inspection", "sort_order": 20, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 3, "tech_pub_id": 1, "section_number": "3.3", "title": "Insulation Test",
     "section_type": "manual_test", "sort_order": 30, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 4, "tech_pub_id": 1, "section_number": "3.4", "title": "Pre-Discharge",
     "section_type": "automated_test", "sort_order": 40, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 5, "tech_pub_id": 1, "section_number": "3.5", "title": "Standard Charge",
     "section_type": "automated_test", "sort_order": 50, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 6, "tech_pub_id": 1, "section_number": "3.6", "title": "Post-Charge Rest",
     "section_type": "automated_test", "sort_order": 60, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 7, "tech_pub_id": 1, "section_number": "3.7", "title": "Capacity Discharge Test",
     "section_type": "automated_test", "sort_order": 70, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 8, "tech_pub_id": 1, "section_number": "3.8", "title": "Post-Test Charge",
     "section_type": "automated_test", "sort_order": 80, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 9, "tech_pub_id": 1, "section_number": "3.9", "title": "Pass/Fail Evaluation",
     "section_type": "evaluation", "sort_order": 90, "is_mandatory": True,
     "condition_type": "always"},

    # --- CMM 33-51-17 (3214-31) ---
    {"id": 10, "tech_pub_id": 2, "section_number": "3.1", "title": "Visual Inspection",
     "section_type": "inspection", "sort_order": 10, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 11, "tech_pub_id": 2, "section_number": "3.2", "title": "Weight Check",
     "section_type": "inspection", "sort_order": 20, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 12, "tech_pub_id": 2, "section_number": "3.3", "title": "Insulation Test",
     "section_type": "manual_test", "sort_order": 30, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 13, "tech_pub_id": 2, "section_number": "3.4",
     "title": "Heating Foil & Thermostat Tests",
     "section_type": "manual_test", "sort_order": 40, "is_mandatory": True,
     "condition_type": "feature_flag", "condition_key": "has_heating_foil",
     "condition_value": "true"},
    {"id": 14, "tech_pub_id": 2, "section_number": "3.5", "title": "Pre-Discharge",
     "section_type": "automated_test", "sort_order": 50, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 15, "tech_pub_id": 2, "section_number": "3.6",
     "title": "Reconditioning Charge",
     "section_type": "automated_test", "sort_order": 60, "is_mandatory": False,
     "condition_type": "age_threshold", "condition_key": "months_since_service",
     "condition_value": "6"},
    {"id": 16, "tech_pub_id": 2, "section_number": "3.7", "title": "Standard Charge",
     "section_type": "automated_test", "sort_order": 70, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 17, "tech_pub_id": 2, "section_number": "3.8", "title": "Post-Charge Rest",
     "section_type": "automated_test", "sort_order": 80, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 18, "tech_pub_id": 2, "section_number": "3.9",
     "title": "Capacity Discharge Test",
     "section_type": "automated_test", "sort_order": 90, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 19, "tech_pub_id": 2, "section_number": "3.10",
     "title": "Post-Partial Charge",
     "section_type": "automated_test", "sort_order": 100, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 20, "tech_pub_id": 2, "section_number": "3.11",
     "title": "Pass/Fail Evaluation",
     "section_type": "evaluation", "sort_order": 110, "is_mandatory": True,
     "condition_type": "always"},

    # --- CMM 33-51-22 (301-3017) ---
    {"id": 21, "tech_pub_id": 3, "section_number": "3.1", "title": "Visual Inspection",
     "section_type": "inspection", "sort_order": 10, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 22, "tech_pub_id": 3, "section_number": "3.2", "title": "Weight Check",
     "section_type": "inspection", "sort_order": 20, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 23, "tech_pub_id": 3, "section_number": "3.3", "title": "Insulation Test",
     "section_type": "manual_test", "sort_order": 30, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 24, "tech_pub_id": 3, "section_number": "3.4", "title": "Pre-Discharge",
     "section_type": "automated_test", "sort_order": 40, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 25, "tech_pub_id": 3, "section_number": "3.5", "title": "Standard Charge",
     "section_type": "automated_test", "sort_order": 50, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 26, "tech_pub_id": 3, "section_number": "3.6", "title": "Post-Charge Rest",
     "section_type": "automated_test", "sort_order": 60, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 27, "tech_pub_id": 3, "section_number": "3.7",
     "title": "Capacity Discharge Test",
     "section_type": "automated_test", "sort_order": 70, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 28, "tech_pub_id": 3, "section_number": "3.8",
     "title": "Fast Discharge Test",
     "section_type": "automated_test", "sort_order": 80, "is_mandatory": False,
     "condition_type": "feature_flag", "condition_key": "has_fast_discharge",
     "condition_value": "true"},
    {"id": 29, "tech_pub_id": 3, "section_number": "3.9",
     "title": "Post-Test Charge",
     "section_type": "automated_test", "sort_order": 90, "is_mandatory": True,
     "condition_type": "always"},
    {"id": 30, "tech_pub_id": 3, "section_number": "3.10",
     "title": "Pass/Fail Evaluation",
     "section_type": "evaluation", "sort_order": 100, "is_mandatory": True,
     "condition_type": "always"},
]


# =============================================================================
# PROCEDURE STEPS (atomic units of work within each section)
# =============================================================================

SEED_PROCEDURE_STEPS = [
    # --- CMM 33-51-01 (3301-31) Visual Inspection (section_id=1) ---
    {"section_id": 1, "step_number": 1, "step_type": "visual_check",
     "label": "External Condition", "description": "Inspect for cracks, corrosion, electrolyte leakage",
     "param_source": "fixed", "is_automated": False, "sort_order": 1,
     "pass_criteria_type": "boolean", "measurement_key": "visual_pass"},
    {"section_id": 1, "step_number": 2, "step_type": "record_value",
     "label": "Inspection Notes", "description": "Record any anomalies",
     "param_source": "fixed", "is_automated": False, "sort_order": 2},

    # --- CMM 33-51-01 Weight Check (section_id=2) ---
    {"section_id": 2, "step_number": 1, "step_type": "measure_weight",
     "label": "Weight Measurement", "description": "Weigh battery on calibrated scale",
     "param_source": "fixed", "is_automated": False, "sort_order": 1,
     "measurement_key": "weight_kg", "measurement_unit": "kg", "measurement_label": "Battery Weight"},

    # --- CMM 33-51-01 Insulation Test (section_id=3) ---
    {"section_id": 3, "step_number": 1, "step_type": "measure_resistance",
     "label": "Insulation Resistance", "description": "Apply 500VDC between terminals and case",
     "param_source": "fixed", "param_overrides": json.dumps({"test_voltage_vdc": 500}),
     "is_automated": False, "sort_order": 1,
     "pass_criteria_type": "min_value",
     "pass_criteria_value": json.dumps({"min": 2.0, "unit": "MOhm"}),
     "measurement_key": "insulation_resistance_mohm", "measurement_unit": "MOhm",
     "measurement_label": "Insulation Resistance",
     "requires_tools": json.dumps(["insulation_tester"])},

    # --- CMM 33-51-01 Pre-Discharge (section_id=4) ---
    {"section_id": 4, "step_number": 1, "step_type": "discharge",
     "label": "Pre-Discharge", "description": "Discharge to end voltage before charging",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 30.0},
    {"section_id": 4, "step_number": 2, "step_type": "rest",
     "label": "Pre-Discharge Rest", "description": "Cool-down rest after discharge",
     "param_source": "fixed", "param_overrides": json.dumps({"duration_min": 60}),
     "is_automated": True, "sort_order": 2, "estimated_duration_min": 60.0},

    # --- CMM 33-51-01 Standard Charge (section_id=5) ---
    {"section_id": 5, "step_number": 1, "step_type": "charge",
     "label": "Standard Charge", "description": "Charge per EEPROM parameters",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 270.0},

    # --- CMM 33-51-01 Post-Charge Rest (section_id=6) ---
    {"section_id": 6, "step_number": 1, "step_type": "rest",
     "label": "Post-Charge Rest", "description": "Rest before capacity discharge",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 240.0},

    # --- CMM 33-51-01 Capacity Discharge (section_id=7) ---
    {"section_id": 7, "step_number": 1, "step_type": "discharge",
     "label": "Capacity Discharge", "description": "Timed capacity discharge to end voltage",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 60.0,
     "pass_criteria_type": "min_value",
     "pass_criteria_value": json.dumps({"min": 80, "unit": "pct"}),
     "measurement_key": "capacity_pct"},

    # --- CMM 33-51-01 Post-Test Charge (section_id=8) ---
    {"section_id": 8, "step_number": 1, "step_type": "charge",
     "label": "Post-Test Charge", "description": "Return charge after test for storage",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 270.0},

    # --- CMM 33-51-01 Evaluation (section_id=9) ---
    {"section_id": 9, "step_number": 1, "step_type": "evaluate_result",
     "label": "Pass/Fail Determination", "description": "Evaluate overall test result",
     "param_source": "fixed", "is_automated": False, "sort_order": 1},

    # --- CMM 33-51-17 (3214-31) Visual Inspection (section_id=10) ---
    {"section_id": 10, "step_number": 1, "step_type": "visual_check",
     "label": "External Condition", "description": "Inspect for cracks, corrosion, electrolyte leakage",
     "param_source": "fixed", "is_automated": False, "sort_order": 1,
     "pass_criteria_type": "boolean", "measurement_key": "visual_pass"},
    {"section_id": 10, "step_number": 2, "step_type": "record_value",
     "label": "Inspection Notes", "description": "Record any anomalies",
     "param_source": "fixed", "is_automated": False, "sort_order": 2},

    # --- CMM 33-51-17 Weight Check (section_id=11) ---
    {"section_id": 11, "step_number": 1, "step_type": "measure_weight",
     "label": "Weight Measurement", "description": "Weigh battery on calibrated scale",
     "param_source": "fixed", "is_automated": False, "sort_order": 1,
     "measurement_key": "weight_kg", "measurement_unit": "kg", "measurement_label": "Battery Weight"},

    # --- CMM 33-51-17 Insulation Test (section_id=12) ---
    {"section_id": 12, "step_number": 1, "step_type": "measure_resistance",
     "label": "Insulation Resistance", "description": "Apply 500VDC between terminals and case",
     "param_source": "fixed", "param_overrides": json.dumps({"test_voltage_vdc": 500}),
     "is_automated": False, "sort_order": 1,
     "pass_criteria_type": "min_value",
     "pass_criteria_value": json.dumps({"min": 2.0, "unit": "MOhm"}),
     "measurement_key": "insulation_resistance_mohm", "measurement_unit": "MOhm",
     "measurement_label": "Insulation Resistance",
     "requires_tools": json.dumps(["insulation_tester"])},

    # --- CMM 33-51-17 Heating Foil & Thermostat (section_id=13) ---
    {"section_id": 13, "step_number": 1, "step_type": "measure_resistance",
     "label": "Heating Foil Resistance",
     "description": "Measure heating foil resistance (nominal 14.4 Ohm +/- 20%)",
     "param_source": "fixed",
     "param_overrides": json.dumps({"nominal_ohm": 14.4, "tolerance_pct": 20}),
     "is_automated": False, "sort_order": 1,
     "pass_criteria_type": "range",
     "pass_criteria_value": json.dumps({"min": 11.52, "max": 17.28, "unit": "Ohm"}),
     "measurement_key": "heating_foil_resistance_ohm", "measurement_unit": "Ohm",
     "measurement_label": "Heating Foil Resistance",
     "requires_tools": json.dumps(["multimeter"])},
    {"section_id": 13, "step_number": 2, "step_type": "measure_temperature",
     "label": "Thermostat Open Temperature",
     "description": "Record temperature at which thermostat opens",
     "param_source": "fixed", "is_automated": False, "sort_order": 2,
     "measurement_key": "thermostat_open_temp_c", "measurement_unit": "C",
     "measurement_label": "Thermostat Open Temp",
     "requires_tools": json.dumps(["thermometer"])},
    {"section_id": 13, "step_number": 3, "step_type": "measure_temperature",
     "label": "Thermostat Close Temperature",
     "description": "Record temperature at which thermostat closes",
     "param_source": "fixed", "is_automated": False, "sort_order": 3,
     "measurement_key": "thermostat_close_temp_c", "measurement_unit": "C",
     "measurement_label": "Thermostat Close Temp",
     "requires_tools": json.dumps(["thermometer"])},
    {"section_id": 13, "step_number": 4, "step_type": "functional_check",
     "label": "Thermostat Function",
     "description": "Verify thermostat open temp > close temp (hysteresis check)",
     "param_source": "previous_step", "is_automated": False, "sort_order": 4,
     "pass_criteria_type": "boolean", "measurement_key": "thermostat_pass"},
    {"section_id": 13, "step_number": 5, "step_type": "measure_resistance",
     "label": "Temperature Sensor (NTC)",
     "description": "Measure NTC temperature sensor resistance",
     "param_source": "fixed", "is_automated": False, "sort_order": 5,
     "pass_criteria_type": "range",
     "pass_criteria_value": json.dumps({"min": 1.0, "max": 100.0, "unit": "kOhm"}),
     "measurement_key": "temp_sensor_resistance_kohm", "measurement_unit": "kOhm",
     "measurement_label": "NTC Resistance",
     "requires_tools": json.dumps(["multimeter"])},

    # --- CMM 33-51-17 Pre-Discharge (section_id=14) ---
    {"section_id": 14, "step_number": 1, "step_type": "discharge",
     "label": "Pre-Discharge", "description": "Discharge to end voltage",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 480.0},
    {"section_id": 14, "step_number": 2, "step_type": "rest",
     "label": "Pre-Discharge Rest", "description": "Cool-down rest",
     "param_source": "fixed", "param_overrides": json.dumps({"duration_min": 60}),
     "is_automated": True, "sort_order": 2, "estimated_duration_min": 60.0},

    # --- CMM 33-51-17 Reconditioning (section_id=15) ---
    {"section_id": 15, "step_number": 1, "step_type": "charge",
     "label": "Reconditioning Charge", "description": "Extended charge for reconditioning",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 840.0},

    # --- CMM 33-51-17 Standard Charge (section_id=16) ---
    {"section_id": 16, "step_number": 1, "step_type": "charge",
     "label": "Standard Charge", "description": "Standard 16h charge per EEPROM",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 960.0},

    # --- CMM 33-51-17 Post-Charge Rest (section_id=17) ---
    {"section_id": 17, "step_number": 1, "step_type": "rest",
     "label": "Post-Charge Rest", "description": "Rest before capacity discharge",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 240.0},

    # --- CMM 33-51-17 Capacity Discharge (section_id=18) ---
    {"section_id": 18, "step_number": 1, "step_type": "discharge",
     "label": "Capacity Discharge", "description": "Timed capacity discharge at C/5",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 480.0,
     "pass_criteria_type": "min_value",
     "pass_criteria_value": json.dumps({"min": 80, "unit": "pct"}),
     "measurement_key": "capacity_pct"},

    # --- CMM 33-51-17 Post-Partial Charge (section_id=19) ---
    {"section_id": 19, "step_number": 1, "step_type": "charge",
     "label": "Post-Partial Charge", "description": "Partial charge for storage",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 270.0},

    # --- CMM 33-51-17 Evaluation (section_id=20) ---
    {"section_id": 20, "step_number": 1, "step_type": "evaluate_result",
     "label": "Pass/Fail Determination", "description": "Evaluate overall test result",
     "param_source": "fixed", "is_automated": False, "sort_order": 1},

    # --- CMM 33-51-22 (301-3017) Visual Inspection (section_id=21) ---
    {"section_id": 21, "step_number": 1, "step_type": "visual_check",
     "label": "External Condition", "description": "Inspect for cracks, corrosion, electrolyte leakage",
     "param_source": "fixed", "is_automated": False, "sort_order": 1,
     "pass_criteria_type": "boolean", "measurement_key": "visual_pass"},

    # --- CMM 33-51-22 Weight Check (section_id=22) ---
    {"section_id": 22, "step_number": 1, "step_type": "measure_weight",
     "label": "Weight Measurement", "description": "Weigh battery",
     "param_source": "fixed", "is_automated": False, "sort_order": 1,
     "measurement_key": "weight_kg", "measurement_unit": "kg", "measurement_label": "Battery Weight"},

    # --- CMM 33-51-22 Insulation Test (section_id=23) ---
    {"section_id": 23, "step_number": 1, "step_type": "measure_resistance",
     "label": "Insulation Resistance", "description": "Apply 500VDC",
     "param_source": "fixed", "param_overrides": json.dumps({"test_voltage_vdc": 500}),
     "is_automated": False, "sort_order": 1,
     "pass_criteria_type": "min_value",
     "pass_criteria_value": json.dumps({"min": 2.0, "unit": "MOhm"}),
     "measurement_key": "insulation_resistance_mohm", "measurement_unit": "MOhm",
     "requires_tools": json.dumps(["insulation_tester"])},

    # --- CMM 33-51-22 Pre-Discharge (section_id=24) ---
    {"section_id": 24, "step_number": 1, "step_type": "discharge",
     "label": "Pre-Discharge", "description": "Discharge to end voltage",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 480.0},
    {"section_id": 24, "step_number": 2, "step_type": "rest",
     "label": "Pre-Discharge Rest", "description": "Cool-down rest",
     "param_source": "fixed", "param_overrides": json.dumps({"duration_min": 60}),
     "is_automated": True, "sort_order": 2, "estimated_duration_min": 60.0},

    # --- CMM 33-51-22 Standard Charge (section_id=25) ---
    {"section_id": 25, "step_number": 1, "step_type": "charge",
     "label": "Standard Charge", "description": "16h charge per EEPROM",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 960.0},

    # --- CMM 33-51-22 Post-Charge Rest (section_id=26) ---
    {"section_id": 26, "step_number": 1, "step_type": "rest",
     "label": "Post-Charge Rest", "description": "Rest before capacity discharge",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 60.0},

    # --- CMM 33-51-22 Capacity Discharge (section_id=27) ---
    {"section_id": 27, "step_number": 1, "step_type": "discharge",
     "label": "Capacity Discharge", "description": "Timed capacity discharge at C/5",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 480.0,
     "pass_criteria_type": "min_value",
     "pass_criteria_value": json.dumps({"min": 80, "unit": "pct"}),
     "measurement_key": "capacity_pct"},

    # --- CMM 33-51-22 Fast Discharge (section_id=28) ---
    {"section_id": 28, "step_number": 1, "step_type": "charge",
     "label": "Re-Charge Before Fast Discharge",
     "description": "Charge before fast discharge test",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 960.0},
    {"section_id": 28, "step_number": 2, "step_type": "rest",
     "label": "Rest Before Fast Discharge", "description": "Rest period",
     "param_source": "fixed", "param_overrides": json.dumps({"duration_min": 60}),
     "is_automated": True, "sort_order": 2, "estimated_duration_min": 60.0},
    {"section_id": 28, "step_number": 3, "step_type": "discharge",
     "label": "Fast Discharge", "description": "High-rate discharge test at 4A",
     "param_source": "eeprom",
     "param_overrides": json.dumps({"current_ma": 4000, "voltage_min_mv": 5000}),
     "is_automated": True, "sort_order": 3, "estimated_duration_min": 30.0,
     "pass_criteria_type": "min_duration",
     "pass_criteria_value": json.dumps({"min": 15, "unit": "min"}),
     "measurement_key": "fast_discharge_duration_min"},

    # --- CMM 33-51-22 Post-Test Charge (section_id=29) ---
    {"section_id": 29, "step_number": 1, "step_type": "charge",
     "label": "Post-Test Charge", "description": "Return charge for storage",
     "param_source": "eeprom", "is_automated": True, "sort_order": 1,
     "estimated_duration_min": 960.0},

    # --- CMM 33-51-22 Evaluation (section_id=30) ---
    {"section_id": 30, "step_number": 1, "step_type": "evaluate_result",
     "label": "Pass/Fail Determination", "description": "Evaluate overall test result",
     "param_source": "fixed", "is_automated": False, "sort_order": 1},
]


# =============================================================================
# BATTERY PROFILE FEATURE FLAGS (v2.0.0 — replaces hardcoded _has_heating_foil)
# =============================================================================

SEED_PROFILE_FEATURE_FLAGS = {
    # 3301-31 profiles (ids 1-3): no heating foil
    1: {"has_heating_foil": False, "has_thermostat": False, "has_temp_sensor": False},
    2: {"has_heating_foil": False, "has_thermostat": False, "has_temp_sensor": False},
    3: {"has_heating_foil": False, "has_thermostat": False, "has_temp_sensor": False},
    # 3214-31 profiles (ids 4-5): has heating foil, thermostat, temp sensor
    4: {"has_heating_foil": True, "has_thermostat": True, "has_temp_sensor": True},
    5: {"has_heating_foil": True, "has_thermostat": True, "has_temp_sensor": True},
    # 301-3017 profiles (ids 6-7): has fast discharge
    6: {"has_heating_foil": False, "has_fast_discharge": True},
    7: {"has_heating_foil": False, "has_fast_discharge": True},
}

# Tech pub ID mapping for profiles
SEED_PROFILE_TECH_PUB_IDS = {
    1: 1, 2: 1, 3: 1,  # 3301-31 → CMM 33-51-01
    4: 2, 5: 2,          # 3214-31 → CMM 33-51-17
    6: 3, 7: 3,          # 301-3017 → CMM 33-51-22
}


# =============================================================================
# seed_if_empty(db) — populate all tables when they are empty
# =============================================================================

async def seed_if_empty(db):
    """Populate the database with seed data if the tables are empty.

    Inserts in FK-dependency order:
        customers -> tech_pubs -> battery_profiles -> recipes -> tools ->
        station_calibrations -> work_orders -> work_order_items ->
        work_jobs -> work_job_tasks
    """

    async def _count(table: str) -> int:
        row = await db.execute(f"SELECT COUNT(*) FROM {table}")
        result = await row.fetchone()
        return result[0] if result else 0

    # ------------------------------------------------------------------
    # 1. CUSTOMERS
    # ------------------------------------------------------------------
    if await _count("customers") == 0:
        log.info("Seeding customers (%d records)...", len(SEED_CUSTOMERS))
        for c in SEED_CUSTOMERS:
            await db.execute(
                """INSERT INTO customers
                   (id, name, customer_code, contact_person, email, phone,
                    address_line1, notes, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (c["id"], c["name"], c["customer_code"], c["contact_person"],
                 c["email"], c["phone"], c["address_line1"], c["notes"],
                 c["is_active"], c["created_at"]),
            )

    # ------------------------------------------------------------------
    # 2. TECH PUBS
    # ------------------------------------------------------------------
    if await _count("tech_pubs") == 0:
        log.info("Seeding tech_pubs (%d records)...", len(SEED_TECH_PUBS))
        for tp in SEED_TECH_PUBS:
            await db.execute(
                """INSERT INTO tech_pubs
                   (id, cmm_number, title, revision, revision_date,
                    applicable_part_numbers, ata_chapter, issued_by,
                    notes, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tp["id"], tp["cmm_number"], tp["title"], tp["revision"],
                 tp["revision_date"],
                 json.dumps(tp["applicable_part_numbers"]),
                 tp["ata_chapter"], tp["issued_by"], tp["notes"],
                 tp["is_active"]),
            )

    # ------------------------------------------------------------------
    # 3. BATTERY PROFILES
    # ------------------------------------------------------------------
    if await _count("battery_profiles") == 0:
        log.info("Seeding battery_profiles (%d records)...", len(SEED_PROFILES))
        for p in SEED_PROFILES:
            await db.execute(
                """INSERT INTO battery_profiles
                   (id, part_number, amendment, description, manufacturer,
                    manufacturer_code, nominal_voltage_v, capacity_ah,
                    num_cells, chemistry, std_charge_current_ma,
                    std_charge_duration_h, std_charge_voltage_limit_mv,
                    cap_test_current_a, cap_test_voltage_min_mv,
                    cap_test_duration_min, pre_discharge_current_a,
                    pre_discharge_end_voltage_mv, post_charge_current_ma,
                    post_charge_duration_h, rest_before_cap_test_min,
                    fast_discharge_enabled, fast_discharge_current_a,
                    fast_discharge_end_voltage_mv, fast_discharge_duration_min,
                    max_temp_c, discharge_max_temp_c, emergency_temp_max_c,
                    pass_min_minutes, pass_min_capacity_pct, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                           ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (p["id"], p["part_number"], p["amendment"], p["description"],
                 p["manufacturer"], p["manufacturer_code"],
                 p["nominal_voltage_v"], p["capacity_ah"], p["num_cells"],
                 p["chemistry"], p["std_charge_current_ma"],
                 p["std_charge_duration_h"], p["std_charge_voltage_limit_mv"],
                 p["cap_test_current_a"], p["cap_test_voltage_min_mv"],
                 p["cap_test_duration_min"], p["pre_discharge_current_a"],
                 p["pre_discharge_end_voltage_mv"], p["post_charge_current_ma"],
                 p["post_charge_duration_h"], p["rest_before_cap_test_min"],
                 p["fast_discharge_enabled"],
                 p.get("fast_discharge_current_a"),
                 p.get("fast_discharge_end_voltage_mv"),
                 p.get("fast_discharge_duration_min"),
                 p["max_temp_c"], p["discharge_max_temp_c"],
                 p["emergency_temp_max_c"], p["pass_min_minutes"],
                 p["pass_min_capacity_pct"], p["is_active"]),
            )

    # ------------------------------------------------------------------
    # 4. RECIPES
    # ------------------------------------------------------------------
    if await _count("recipes") == 0:
        log.info("Seeding recipes (%d records)...", len(SEED_RECIPES))
        for r in SEED_RECIPES:
            await db.execute(
                """INSERT INTO recipes
                   (id, tech_pub_id, cmm_reference, name, description,
                    recipe_type, is_default, applicable_part_numbers,
                    steps, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r["id"], r["tech_pub_id"], r["cmm_reference"], r["name"],
                 r["description"], r["recipe_type"], r["is_default"],
                 json.dumps(r["applicable_part_numbers"]),
                 json.dumps(r["steps"]),
                 r["is_active"]),
            )

    # ------------------------------------------------------------------
    # 5. TOOLS
    # ------------------------------------------------------------------
    if await _count("tools") == 0:
        log.info("Seeding tools (%d records)...", len(SEED_TOOLS))
        for t in SEED_TOOLS:
            await db.execute(
                """INSERT INTO tools
                   (id, part_number, description, manufacturer, serial_number,
                    calibration_date, valid_until, internal_reference,
                    category, is_active, calibration_certificate,
                    calibrated_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (t["id"], t["part_number"], t["description"],
                 t["manufacturer"], t["serial_number"],
                 t["calibration_date"], t["valid_until"],
                 t["internal_reference"], t["category"], t["is_active"],
                 t["calibration_certificate"], t["calibrated_by"]),
            )

    # ------------------------------------------------------------------
    # 6. STATION CALIBRATIONS
    # ------------------------------------------------------------------
    if await _count("station_calibrations") == 0:
        log.info("Seeding station_calibrations (%d records)...",
                 len(SEED_STATION_CALIBRATIONS))
        for sc in SEED_STATION_CALIBRATIONS:
            await db.execute(
                """INSERT INTO station_calibrations
                   (station_id, unit, model, serial_number,
                    last_calibration_date, next_due_date, calibrated_by,
                    calibration_certificate, result, readings)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sc["station_id"], sc["unit"], sc["model"],
                 sc["serial_number"], sc["last_calibration_date"],
                 sc["next_due_date"], sc["calibrated_by"],
                 sc["calibration_certificate"], sc["result"],
                 json.dumps(sc["readings"])),
            )

    # ------------------------------------------------------------------
    # 7. WORK ORDERS
    # ------------------------------------------------------------------
    if await _count("work_orders") == 0:
        log.info("Seeding work_orders (%d records)...", len(SEED_WORK_ORDERS))
        for wo in SEED_WORK_ORDERS:
            await db.execute(
                """INSERT INTO work_orders
                   (id, work_order_number, customer_reference, customer_id,
                    service_type, priority, status, received_date,
                    completed_date, assigned_technician, customer_notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (wo["id"], wo["work_order_number"],
                 wo["customer_reference"], wo["customer_id"],
                 wo["service_type"], wo["priority"], wo["status"],
                 wo["received_date"], wo.get("completed_date"),
                 wo["assigned_technician"], wo["customer_notes"]),
            )

    # ------------------------------------------------------------------
    # 8. WORK ORDER ITEMS
    # ------------------------------------------------------------------
    if await _count("work_order_items") == 0:
        log.info("Seeding work_order_items (%d records)...",
                 len(SEED_WORK_ORDER_ITEMS))
        for item in SEED_WORK_ORDER_ITEMS:
            await db.execute(
                """INSERT INTO work_order_items
                   (id, work_order_id, serial_number, part_number,
                    revision, amendment, reported_condition, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (item["id"], item["work_order_id"], item["serial_number"],
                 item["part_number"], item["revision"], item["amendment"],
                 item["reported_condition"], item["status"]),
            )

    # ------------------------------------------------------------------
    # 9. WORK JOBS
    # ------------------------------------------------------------------
    if await _count("work_jobs") == 0:
        log.info("Seeding work_jobs (%d records)...", len(SEED_WORK_JOBS))
        for j in SEED_WORK_JOBS:
            await db.execute(
                """INSERT INTO work_jobs
                   (id, work_order_id, work_order_item_id,
                    work_order_number, battery_serial, battery_part_number,
                    battery_amendment, tech_pub_id, tech_pub_cmm,
                    tech_pub_revision, recipe_id, recipe_name,
                    recipe_cmm_ref, station_id, status, started_at,
                    completed_at, started_by, result, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                           ?, ?, ?, ?)""",
                (j["id"], j["work_order_id"], j["work_order_item_id"],
                 j["work_order_number"], j["battery_serial"],
                 j["battery_part_number"], j["battery_amendment"],
                 j["tech_pub_id"], j["tech_pub_cmm"],
                 j["tech_pub_revision"], j["recipe_id"], j["recipe_name"],
                 j["recipe_cmm_ref"], j["station_id"], j["status"],
                 j["started_at"], j["completed_at"], j["started_by"],
                 j["result"], j["created_at"]),
            )

    # ------------------------------------------------------------------
    # 10. WORK JOB TASKS
    # ------------------------------------------------------------------
    if await _count("work_job_tasks") == 0:
        log.info("Seeding work_job_tasks (%d records)...",
                 len(SEED_WORK_JOB_TASKS))
        for t in SEED_WORK_JOB_TASKS:
            await db.execute(
                """INSERT INTO work_job_tasks
                   (id, work_job_id, task_number, step_number, type, label,
                    params, source, tools_used, measured_values,
                    step_result, start_time, end_time, chart_data,
                    data_points, status, result_notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                           ?)""",
                (t["id"], t["work_job_id"], t["task_number"],
                 t["step_number"], t["type"], t["label"],
                 json.dumps(t["params"]), t["source"],
                 json.dumps(t["tools_used"]),
                 json.dumps(t.get("measured_values", {})),
                 t.get("step_result"),
                 t["start_time"], t["end_time"],
                 json.dumps(t["chart_data"]),
                 t["data_points"], t["status"], t["result_notes"]),
            )

    # ------------------------------------------------------------------
    # 11. TECH PUB APPLICABILITY (v2.0.0)
    # ------------------------------------------------------------------
    if await _count("tech_pub_applicability") == 0:
        log.info("Seeding tech_pub_applicability (%d records)...",
                 len(SEED_TECH_PUB_APPLICABILITY))
        for tpa in SEED_TECH_PUB_APPLICABILITY:
            await db.execute(
                """INSERT INTO tech_pub_applicability
                   (tech_pub_id, part_number, amendment)
                   VALUES (?, ?, ?)""",
                (tpa["tech_pub_id"], tpa["part_number"], tpa["amendment"]),
            )

    # ------------------------------------------------------------------
    # 12. TECH PUB SECTIONS (v2.0.0)
    # ------------------------------------------------------------------
    if await _count("tech_pub_sections") == 0:
        log.info("Seeding tech_pub_sections (%d records)...",
                 len(SEED_TECH_PUB_SECTIONS))
        for sec in SEED_TECH_PUB_SECTIONS:
            await db.execute(
                """INSERT INTO tech_pub_sections
                   (id, tech_pub_id, section_number, title, section_type,
                    sort_order, is_mandatory, condition_type,
                    condition_key, condition_value, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (sec["id"], sec["tech_pub_id"], sec["section_number"],
                 sec["title"], sec["section_type"], sec["sort_order"],
                 sec["is_mandatory"], sec["condition_type"],
                 sec.get("condition_key"), sec.get("condition_value")),
            )

    # ------------------------------------------------------------------
    # 13. PROCEDURE STEPS (v2.0.0)
    # ------------------------------------------------------------------
    if await _count("procedure_steps") == 0:
        log.info("Seeding procedure_steps (%d records)...",
                 len(SEED_PROCEDURE_STEPS))
        for step in SEED_PROCEDURE_STEPS:
            await db.execute(
                """INSERT INTO procedure_steps
                   (section_id, step_number, step_type, label, description,
                    param_source, param_overrides, pass_criteria_type,
                    pass_criteria_value, measurement_key, measurement_unit,
                    measurement_label, estimated_duration_min, is_automated,
                    requires_tools, sort_order, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (step["section_id"], step["step_number"], step["step_type"],
                 step["label"], step.get("description"),
                 step.get("param_source", "fixed"),
                 step.get("param_overrides", "{}"),
                 step.get("pass_criteria_type"),
                 step.get("pass_criteria_value"),
                 step.get("measurement_key"),
                 step.get("measurement_unit"),
                 step.get("measurement_label"),
                 step.get("estimated_duration_min", 0),
                 step.get("is_automated", False),
                 step.get("requires_tools", "[]"),
                 step.get("sort_order", 0)),
            )

    # ------------------------------------------------------------------
    # 14. BATTERY PROFILE FEATURE FLAGS + TECH PUB IDS (v2.0.0)
    # ------------------------------------------------------------------
    log.info("Updating battery_profiles with feature_flags and tech_pub_id...")
    for profile_id, flags in SEED_PROFILE_FEATURE_FLAGS.items():
        await db.execute(
            "UPDATE battery_profiles SET feature_flags = ? WHERE id = ?",
            (json.dumps(flags), profile_id),
        )
    for profile_id, tp_id in SEED_PROFILE_TECH_PUB_IDS.items():
        await db.execute(
            "UPDATE battery_profiles SET tech_pub_id = ? WHERE id = ?",
            (tp_id, profile_id),
        )

    # ------------------------------------------------------------------
    # 15. TOOLS — tool_id_display (TID format, v2.0.0)
    # ------------------------------------------------------------------
    log.info("Updating tools with tool_id_display...")
    await db.execute("""
        UPDATE tools SET tool_id_display = 'TID' || printf('%03d', id)
        WHERE tool_id_display IS NULL
    """)

    # ------------------------------------------------------------------
    # 16. STATION EQUIPMENT (from station_calibrations, v2.0.0)
    # ------------------------------------------------------------------
    if await _count("station_equipment") == 0:
        log.info("Seeding station_equipment from station_calibrations...")
        for sid in range(1, 13):
            # PSU
            await db.execute(
                """INSERT OR IGNORE INTO station_equipment
                   (station_id, equipment_role, model, serial_number, ip_address)
                   VALUES (?, 'psu',
                           (SELECT model FROM station_calibrations
                            WHERE station_id = ? AND unit = 'psu'),
                           (SELECT serial_number FROM station_calibrations
                            WHERE station_id = ? AND unit = 'psu'),
                           ?)""",
                (sid, sid, sid, f"192.168.1.{100 + sid}"),
            )
            # DC Load
            await db.execute(
                """INSERT OR IGNORE INTO station_equipment
                   (station_id, equipment_role, model, serial_number, ip_address)
                   VALUES (?, 'dc_load',
                           (SELECT model FROM station_calibrations
                            WHERE station_id = ? AND unit = 'dc_load'),
                           (SELECT serial_number FROM station_calibrations
                            WHERE station_id = ? AND unit = 'dc_load'),
                           ?)""",
                (sid, sid, sid, f"192.168.1.{200 + sid}"),
            )

    await db.commit()
    log.info("Database seeding complete (v2.0.0).")
