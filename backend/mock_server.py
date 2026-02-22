"""
Battery Test Bench - Mock Backend Server (UI/UX Testing Only)
Version: 1.4.2

Changelog:
v1.4.2 (2026-02-20): Added StaticFiles mount for serving frontend build in production;
                      updated entry point to detect and report frontend availability
v1.4.1 (2026-02-18): Reworked PSU & DC Load verification procedures — 20 test points each
                      across 0-16V / 0-8A range with SM-derived accuracy tolerances;
                      added category, expected_value, tolerance_pct, tolerance_abs fields
v1.4.0 (2026-02-18): SQLite persistence — all CRUD endpoints now use aiosqlite;
                      data persists across server restarts; seed data loaded on
                      first run; removed all in-memory MOCK_* data stores
v1.3.5 (2026-02-17): -ΔV peak detection fields in BATTERY_MODELS; ControlCommand
                      accepts delta_v config; realistic NiCd charge curve simulation;
                      WebSocket broadcast filters internal simulation state
v1.3.4 (2026-02-17): Chart data standardized to 10-second measurement intervals;
                      diagnostic connection endpoint for PSU/DC load verification
v1.3.3 (2026-02-17): Expanded battery models — all amendments per tech pub P/N with
                      distinct specs (7 models across 3 CMMs)
v1.3.2 (2026-02-17): Work jobs status filter; completed mock job with full task data
                      (chart_data, tools_used, measured_values, step_result);
                      report endpoint returns assembled job data
v1.3.1 (2026-02-17): Calibration certificate + entity on tools; station calibration
                      data & CRUD for internal PSU/DC load dock calibration
v1.3.0 (2026-02-17): Tech pubs, reworked recipes linked to CMM, calibrated tools,
                      work jobs, tool validity enforcement
v1.2.9 (2026-02-16): Task log storage endpoint; control command accepts duration_min for all modes
v1.2.8 (2026-02-16): Full CRUD endpoints for customers, work orders, battery profiles;
                      work order items with battery assignment to stations; richer mock data
v1.2.7 (2026-02-16): WebSocket fix, updated BATTERY_MODELS with BatteryConfig v1.2.6 fields

Run this instead of the real backend to test the PWA frontend
without any hardware connected. Simulates 12 stations with
realistic data, WebSocket updates, and all REST API endpoints.

Usage:
    cd backend
    pip install fastapi uvicorn websockets aiosqlite
    python mock_server.py

Then in another terminal:
    cd frontend
    npm run dev

Open http://localhost:3001 to test the PWA UI.
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from models import init_db
from seed import seed_if_empty
from database import get_db, execute_one, execute_all, execute_insert, execute_update, json_col, from_json


# =============================================================================
# Simulated Station Data
# =============================================================================

STATES = ["empty", "dock_detected", "ready", "running", "complete", "error"]
PHASES = [
    "idle", "pre_discharge", "pre_rest", "reconditioning", "charging",
    "post_charge_rest", "cap_discharging", "fast_discharging",
    "post_partial_charge", "complete_pass", "complete_fail"
]

BATTERY_MODELS = [
    # --- 3301-31 Original ---
    {
        "format_version": 2, "battery_type": 0, "nominal_capacity_mah": 1700,
        "cell_count": 5, "nominal_voltage_mv": 6000,
        "charge_voltage_limit_mv": 8900, "standard_charge_current_ma": 350,
        "standard_charge_duration_min": 300, "charge_temp_max_c": 45.0,
        "recondition_charge_current_ma": 350, "recondition_charge_duration_min": 300,
        "recondition_storage_threshold_months": 6,
        "cap_test_discharge_current_ma": 5000, "cap_test_end_voltage_mv": 5000,
        "cap_test_max_duration_min": 60, "cap_test_rest_before_min": 240,
        "cap_test_pass_min_minutes": 18, "cap_test_pass_min_capacity_pct": 85,
        "cap_test_voltage_check_time_min": 0, "cap_test_voltage_check_min_mv": 0,
        "fast_discharge_enabled": False, "fast_discharge_current_ma": 0,
        "fast_discharge_end_voltage_mv": 0, "fast_discharge_max_duration_min": 0,
        "fast_discharge_pass_min_minutes": 0, "fast_discharge_rest_before_min": 60,
        "pre_discharge_current_ma": 5000, "pre_discharge_end_voltage_mv": 5000,
        "post_charge_current_ma": 350, "post_charge_duration_min": 300,
        "discharge_temp_max_c": 55.0, "emergency_temp_max_c": 60.0,
        "min_operating_temp_c": -15.0, "absolute_min_voltage_mv": 4500,
        "max_voltage_mv": 9500,
        "age_rest_threshold_months": 24, "age_rest_duration_hours": 24,
        "part_number": "3301-31", "amendment": "",
        "model_description": "DIEHL NiCd 6V 1.7Ah (Original)",
        "manufacturer_code": "D1347",
        "delta_v_enabled": True, "delta_v_threshold_mv": 40,
        "delta_v_peak_hold_time_s": 60, "delta_v_moving_avg_window": 6,
        "delta_v_min_charge_time_min": 30, "delta_v_drop_confirmation_samples": 3,
        "delta_v_max_charge_time_min": 0, "delta_v_temp_contribution_pct": 0,
    },
    # --- 3301-31 Amdt A ---
    {
        "format_version": 2, "battery_type": 0, "nominal_capacity_mah": 1700,
        "cell_count": 5, "nominal_voltage_mv": 6000,
        "charge_voltage_limit_mv": 9000, "standard_charge_current_ma": 400,
        "standard_charge_duration_min": 270, "charge_temp_max_c": 45.0,
        "recondition_charge_current_ma": 400, "recondition_charge_duration_min": 270,
        "recondition_storage_threshold_months": 6,
        "cap_test_discharge_current_ma": 5000, "cap_test_end_voltage_mv": 5000,
        "cap_test_max_duration_min": 60, "cap_test_rest_before_min": 240,
        "cap_test_pass_min_minutes": 18, "cap_test_pass_min_capacity_pct": 90,
        "cap_test_voltage_check_time_min": 0, "cap_test_voltage_check_min_mv": 0,
        "fast_discharge_enabled": False, "fast_discharge_current_ma": 0,
        "fast_discharge_end_voltage_mv": 0, "fast_discharge_max_duration_min": 0,
        "fast_discharge_pass_min_minutes": 0, "fast_discharge_rest_before_min": 60,
        "pre_discharge_current_ma": 5000, "pre_discharge_end_voltage_mv": 5000,
        "post_charge_current_ma": 400, "post_charge_duration_min": 270,
        "discharge_temp_max_c": 55.0, "emergency_temp_max_c": 60.0,
        "min_operating_temp_c": -15.0, "absolute_min_voltage_mv": 4500,
        "max_voltage_mv": 9500,
        "age_rest_threshold_months": 24, "age_rest_duration_hours": 24,
        "part_number": "3301-31", "amendment": "A",
        "model_description": "DIEHL NiCd 6V 1.7Ah",
        "manufacturer_code": "D1347",
        "delta_v_enabled": True, "delta_v_threshold_mv": 40,
        "delta_v_peak_hold_time_s": 60, "delta_v_moving_avg_window": 6,
        "delta_v_min_charge_time_min": 30, "delta_v_drop_confirmation_samples": 3,
        "delta_v_max_charge_time_min": 0, "delta_v_temp_contribution_pct": 0,
    },
    # --- 3301-31 Amdt B ---
    {
        "format_version": 2, "battery_type": 0, "nominal_capacity_mah": 1700,
        "cell_count": 5, "nominal_voltage_mv": 6000,
        "charge_voltage_limit_mv": 9000, "standard_charge_current_ma": 425,
        "standard_charge_duration_min": 240, "charge_temp_max_c": 45.0,
        "recondition_charge_current_ma": 425, "recondition_charge_duration_min": 240,
        "recondition_storage_threshold_months": 6,
        "cap_test_discharge_current_ma": 5000, "cap_test_end_voltage_mv": 5100,
        "cap_test_max_duration_min": 55, "cap_test_rest_before_min": 180,
        "cap_test_pass_min_minutes": 18, "cap_test_pass_min_capacity_pct": 90,
        "cap_test_voltage_check_time_min": 0, "cap_test_voltage_check_min_mv": 0,
        "fast_discharge_enabled": False, "fast_discharge_current_ma": 0,
        "fast_discharge_end_voltage_mv": 0, "fast_discharge_max_duration_min": 0,
        "fast_discharge_pass_min_minutes": 0, "fast_discharge_rest_before_min": 60,
        "pre_discharge_current_ma": 5000, "pre_discharge_end_voltage_mv": 5100,
        "post_charge_current_ma": 425, "post_charge_duration_min": 240,
        "discharge_temp_max_c": 55.0, "emergency_temp_max_c": 60.0,
        "min_operating_temp_c": -15.0, "absolute_min_voltage_mv": 4500,
        "max_voltage_mv": 9500,
        "age_rest_threshold_months": 24, "age_rest_duration_hours": 24,
        "part_number": "3301-31", "amendment": "B",
        "model_description": "DIEHL NiCd 6V 1.7Ah (Rev 2019)",
        "manufacturer_code": "D1347",
        "delta_v_enabled": True, "delta_v_threshold_mv": 40,
        "delta_v_peak_hold_time_s": 60, "delta_v_moving_avg_window": 6,
        "delta_v_min_charge_time_min": 30, "delta_v_drop_confirmation_samples": 3,
        "delta_v_max_charge_time_min": 0, "delta_v_temp_contribution_pct": 0,
    },
    # --- 3214-31 Amdt A ---
    {
        "format_version": 2, "battery_type": 0, "nominal_capacity_mah": 4000,
        "cell_count": 5, "nominal_voltage_mv": 6000,
        "charge_voltage_limit_mv": 8900, "standard_charge_current_ma": 400,
        "standard_charge_duration_min": 960, "charge_temp_max_c": 45.0,
        "recondition_charge_current_ma": 400, "recondition_charge_duration_min": 960,
        "recondition_storage_threshold_months": 6,
        "cap_test_discharge_current_ma": 800, "cap_test_end_voltage_mv": 5000,
        "cap_test_max_duration_min": 480, "cap_test_rest_before_min": 240,
        "cap_test_pass_min_minutes": 270, "cap_test_pass_min_capacity_pct": 80,
        "cap_test_voltage_check_time_min": 0, "cap_test_voltage_check_min_mv": 0,
        "fast_discharge_enabled": False, "fast_discharge_current_ma": 0,
        "fast_discharge_end_voltage_mv": 0, "fast_discharge_max_duration_min": 0,
        "fast_discharge_pass_min_minutes": 0, "fast_discharge_rest_before_min": 60,
        "pre_discharge_current_ma": 800, "pre_discharge_end_voltage_mv": 5000,
        "post_charge_current_ma": 400, "post_charge_duration_min": 960,
        "discharge_temp_max_c": 50.0, "emergency_temp_max_c": 55.0,
        "min_operating_temp_c": -15.0, "absolute_min_voltage_mv": 4500,
        "max_voltage_mv": 9500,
        "age_rest_threshold_months": 24, "age_rest_duration_hours": 24,
        "part_number": "3214-31", "amendment": "A",
        "model_description": "DIEHL NiCd 6V 4Ah (Original)",
        "manufacturer_code": "D1347",
        "delta_v_enabled": True, "delta_v_threshold_mv": 50,
        "delta_v_peak_hold_time_s": 90, "delta_v_moving_avg_window": 6,
        "delta_v_min_charge_time_min": 60, "delta_v_drop_confirmation_samples": 3,
        "delta_v_max_charge_time_min": 0, "delta_v_temp_contribution_pct": 0,
    },
    # --- 3214-31 Amdt B ---
    {
        "format_version": 2, "battery_type": 0, "nominal_capacity_mah": 4000,
        "cell_count": 5, "nominal_voltage_mv": 6000,
        "charge_voltage_limit_mv": 9000, "standard_charge_current_ma": 400,
        "standard_charge_duration_min": 960, "charge_temp_max_c": 45.0,
        "recondition_charge_current_ma": 400, "recondition_charge_duration_min": 960,
        "recondition_storage_threshold_months": 6,
        "cap_test_discharge_current_ma": 800, "cap_test_end_voltage_mv": 5000,
        "cap_test_max_duration_min": 480, "cap_test_rest_before_min": 240,
        "cap_test_pass_min_minutes": 270, "cap_test_pass_min_capacity_pct": 85,
        "cap_test_voltage_check_time_min": 0, "cap_test_voltage_check_min_mv": 0,
        "fast_discharge_enabled": False, "fast_discharge_current_ma": 0,
        "fast_discharge_end_voltage_mv": 0, "fast_discharge_max_duration_min": 0,
        "fast_discharge_pass_min_minutes": 0, "fast_discharge_rest_before_min": 60,
        "pre_discharge_current_ma": 800, "pre_discharge_end_voltage_mv": 5000,
        "post_charge_current_ma": 400, "post_charge_duration_min": 960,
        "discharge_temp_max_c": 55.0, "emergency_temp_max_c": 60.0,
        "min_operating_temp_c": -15.0, "absolute_min_voltage_mv": 4500,
        "max_voltage_mv": 9500,
        "age_rest_threshold_months": 24, "age_rest_duration_hours": 24,
        "part_number": "3214-31", "amendment": "B",
        "model_description": "DIEHL NiCd 6V 4Ah",
        "manufacturer_code": "D1347",
        "delta_v_enabled": True, "delta_v_threshold_mv": 50,
        "delta_v_peak_hold_time_s": 90, "delta_v_moving_avg_window": 6,
        "delta_v_min_charge_time_min": 60, "delta_v_drop_confirmation_samples": 3,
        "delta_v_max_charge_time_min": 0, "delta_v_temp_contribution_pct": 0,
    },
    # --- 301-3017 Original ---
    {
        "format_version": 2, "battery_type": 0, "nominal_capacity_mah": 2300,
        "cell_count": 5, "nominal_voltage_mv": 6000,
        "charge_voltage_limit_mv": 9000, "standard_charge_current_ma": 230,
        "standard_charge_duration_min": 960, "charge_temp_max_c": 45.0,
        "recondition_charge_current_ma": 230, "recondition_charge_duration_min": 960,
        "recondition_storage_threshold_months": 6,
        "cap_test_discharge_current_ma": 460, "cap_test_end_voltage_mv": 5000,
        "cap_test_max_duration_min": 480, "cap_test_rest_before_min": 60,
        "cap_test_pass_min_minutes": 270, "cap_test_pass_min_capacity_pct": 85,
        "cap_test_voltage_check_time_min": 0, "cap_test_voltage_check_min_mv": 0,
        "fast_discharge_enabled": True, "fast_discharge_current_ma": 4000,
        "fast_discharge_end_voltage_mv": 5000, "fast_discharge_max_duration_min": 60,
        "fast_discharge_pass_min_minutes": 20, "fast_discharge_rest_before_min": 60,
        "pre_discharge_current_ma": 460, "pre_discharge_end_voltage_mv": 5000,
        "post_charge_current_ma": 230, "post_charge_duration_min": 960,
        "discharge_temp_max_c": 55.0, "emergency_temp_max_c": 60.0,
        "min_operating_temp_c": -15.0, "absolute_min_voltage_mv": 4500,
        "max_voltage_mv": 9500,
        "age_rest_threshold_months": 24, "age_rest_duration_hours": 24,
        "part_number": "301-3017", "amendment": "",
        "model_description": "Cobham NiCd 6V 2.3Ah (Original)",
        "manufacturer_code": "F6175",
        "delta_v_enabled": True, "delta_v_threshold_mv": 45,
        "delta_v_peak_hold_time_s": 90, "delta_v_moving_avg_window": 6,
        "delta_v_min_charge_time_min": 45, "delta_v_drop_confirmation_samples": 3,
        "delta_v_max_charge_time_min": 0, "delta_v_temp_contribution_pct": 0,
    },
    # --- 301-3017 Amdt A ---
    {
        "format_version": 2, "battery_type": 0, "nominal_capacity_mah": 2300,
        "cell_count": 5, "nominal_voltage_mv": 6000,
        "charge_voltage_limit_mv": 9100, "standard_charge_current_ma": 230,
        "standard_charge_duration_min": 840, "charge_temp_max_c": 45.0,
        "recondition_charge_current_ma": 230, "recondition_charge_duration_min": 840,
        "recondition_storage_threshold_months": 6,
        "cap_test_discharge_current_ma": 460, "cap_test_end_voltage_mv": 5100,
        "cap_test_max_duration_min": 450, "cap_test_rest_before_min": 60,
        "cap_test_pass_min_minutes": 260, "cap_test_pass_min_capacity_pct": 85,
        "cap_test_voltage_check_time_min": 0, "cap_test_voltage_check_min_mv": 0,
        "fast_discharge_enabled": True, "fast_discharge_current_ma": 4600,
        "fast_discharge_end_voltage_mv": 5100, "fast_discharge_max_duration_min": 55,
        "fast_discharge_pass_min_minutes": 18, "fast_discharge_rest_before_min": 60,
        "pre_discharge_current_ma": 460, "pre_discharge_end_voltage_mv": 5100,
        "post_charge_current_ma": 230, "post_charge_duration_min": 840,
        "discharge_temp_max_c": 55.0, "emergency_temp_max_c": 60.0,
        "min_operating_temp_c": -15.0, "absolute_min_voltage_mv": 4500,
        "max_voltage_mv": 9500,
        "age_rest_threshold_months": 24, "age_rest_duration_hours": 24,
        "part_number": "301-3017", "amendment": "A",
        "model_description": "Cobham NiCd 6V 2.3Ah (Rev 2023)",
        "manufacturer_code": "F6175",
        "delta_v_enabled": True, "delta_v_threshold_mv": 45,
        "delta_v_peak_hold_time_s": 90, "delta_v_moving_avg_window": 6,
        "delta_v_min_charge_time_min": 45, "delta_v_drop_confirmation_samples": 3,
        "delta_v_max_charge_time_min": 0, "delta_v_temp_contribution_pct": 0,
    },
]


def _make_station(station_id: int) -> dict:
    """Generate initial mock station data"""
    if station_id <= 4:
        state = "running"
        phase = random.choice(["charging", "cap_discharging", "post_charge_rest", "pre_discharge"])
        model = BATTERY_MODELS[(station_id - 1) % len(BATTERY_MODELS)]
        voltage = random.randint(5800, 7200)
        current = model["standard_charge_current_ma"] if "charg" in phase else model["cap_test_discharge_current_ma"]
    elif station_id <= 8:
        state = "ready"
        phase = "idle"
        model = BATTERY_MODELS[(station_id - 1) % len(BATTERY_MODELS)]
        voltage = random.randint(5500, 6500)
        current = 0
    elif station_id <= 10:
        state = "complete"
        phase = "complete_pass" if station_id == 9 else "complete_fail"
        model = BATTERY_MODELS[(station_id - 1) % len(BATTERY_MODELS)]
        voltage = random.randint(5800, 6200)
        current = 0
    elif station_id == 11:
        state = "error"
        phase = "idle"
        model = BATTERY_MODELS[0]
        voltage = 0
        current = 0
    else:
        state = "empty"
        phase = "idle"
        model = None
        voltage = None
        current = None

    # Determine work_job_id for stations with active work jobs
    if station_id == 1:
        work_job_id = 1
    elif station_id == 2:
        work_job_id = 2
    else:
        work_job_id = None

    return {
        "station_id": station_id,
        "state": state,
        "temperature_c": round(random.uniform(22.0, 38.0), 1) if state != "empty" else None,
        "temperature_valid": state != "empty",
        "voltage_mv": voltage,
        "current_ma": current,
        "eeprom_present": state != "empty",
        "error_message": "Temperature sensor lost" if state == "error" else None,
        "session_id": station_id * 100 if state == "running" else None,
        "work_order_item_id": station_id * 10 if state in ("running", "complete") else None,
        "work_job_id": work_job_id,
        "test_phase": phase,
        "elapsed_time_s": random.randint(60, 36000) if state == "running" else None,
        "battery_config": model,
    }


_stations = {i: _make_station(i) for i in range(1, 13)}
_ws_clients: List[WebSocket] = []


def _update_stations():
    """Simulate station data changes with realistic NiCd charge curves"""
    for sid, s in _stations.items():
        if s["state"] == "running":
            if s["elapsed_time_s"] is not None:
                s["elapsed_time_s"] += 1

            # --- Realistic NiCd charge curve simulation ---
            if s.get("test_phase") == "charging" and s.get("_charge_sim"):
                sim = s["_charge_sim"]
                sim["tick_count"] += 1
                t = sim["tick_count"]
                start_v = sim["start_voltage_mv"]
                start_temp = sim["start_temp_c"]
                peak_v = sim["target_peak_mv"]

                # Compressed timing for UI testing (real charges take hours)
                # Peak at ~5 min (300 ticks), drop starts ~5.5 min, full drop by ~8 min
                PEAK_TICK = 300
                DROP_START = 330
                DROP_END = 480
                cell_count = sim.get("cell_count", 5)

                if t <= PEAK_TICK:
                    # Rising phase: S-curve from start to peak
                    frac = t / PEAK_TICK
                    smooth = 3 * frac ** 2 - 2 * frac ** 3  # ease in-out
                    v = start_v + int((peak_v - start_v) * smooth)
                    temp_rise = 3.0 * smooth
                    s["temperature_c"] = round(start_temp + temp_rise + random.uniform(-0.2, 0.2), 1)
                elif t <= DROP_START:
                    # Plateau near peak
                    v = peak_v
                    s["temperature_c"] = round(start_temp + 3.0 + (t - PEAK_TICK) * 0.02 + random.uniform(-0.2, 0.2), 1)
                elif t <= DROP_END:
                    # Drop phase: voltage decreases (50 mV/cell total)
                    drop_frac = (t - DROP_START) / (DROP_END - DROP_START)
                    total_drop = cell_count * 50
                    v = peak_v - int(total_drop * drop_frac)
                    s["temperature_c"] = round(start_temp + 3.0 + (t - PEAK_TICK) * 0.04 + random.uniform(-0.2, 0.2), 1)
                else:
                    # Sustained overcharge (if not stopped by -ΔV)
                    total_drop = cell_count * 50
                    v = peak_v - total_drop - int((t - DROP_END) * 0.5)
                    s["temperature_c"] = round(start_temp + 5.0 + (t - PEAK_TICK) * 0.05 + random.uniform(-0.3, 0.3), 1)

                # ADC noise ±5mV
                v += random.randint(-5, 5)
                s["voltage_mv"] = max(5000, min(9500, v))

            else:
                # Non-charge running states: random fluctuation
                if s["temperature_c"]:
                    s["temperature_c"] = round(s["temperature_c"] + random.uniform(-0.3, 0.3), 1)
                    s["temperature_c"] = max(20.0, min(50.0, s["temperature_c"]))
                if s["voltage_mv"]:
                    s["voltage_mv"] += random.randint(-20, 20)
                    s["voltage_mv"] = max(5000, min(9000, s["voltage_mv"]))


# =============================================================================
# Station Calibration Procedures (static data, used by frontend)
# =============================================================================

# PSU Verification Procedure (SPD1168X: 0-16V, 0-8A)
# 20 test points: 14 voltage accuracy (no load) + 6 voltage regulation under load
# Accuracy spec: ±(0.05% + 10mV) voltage, ±(0.1% + 10mA) current
# Equipment required: 6.5-digit DMM (e.g. Siglent SDM3065X), calibrated shunt/clamp for current
PSU_CAL_PROCEDURE = [
    # -- Voltage accuracy (no load, output ON, current limit = 0.1A) --
    {"step": 1, "category": "voltage", "label": "Set PSU to 0.100 V / 0.1 A",
     "set_voltage_v": 0.1, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 0.1, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify minimum voltage accuracy"},
    {"step": 2, "category": "voltage", "label": "Set PSU to 0.500 V / 0.1 A",
     "set_voltage_v": 0.5, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 0.5, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify low-end voltage accuracy"},
    {"step": 3, "category": "voltage", "label": "Set PSU to 1.000 V / 0.1 A",
     "set_voltage_v": 1.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 1.0, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify 1 V accuracy"},
    {"step": 4, "category": "voltage", "label": "Set PSU to 2.000 V / 0.1 A",
     "set_voltage_v": 2.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 2.0, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify 2 V accuracy"},
    {"step": 5, "category": "voltage", "label": "Set PSU to 3.000 V / 0.1 A",
     "set_voltage_v": 3.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 3.0, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify 3 V accuracy"},
    {"step": 6, "category": "voltage", "label": "Set PSU to 4.000 V / 0.1 A",
     "set_voltage_v": 4.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 4.0, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify 4 V accuracy"},
    {"step": 7, "category": "voltage", "label": "Set PSU to 6.000 V / 0.1 A",
     "set_voltage_v": 6.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 6.0, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify 6 V accuracy (NiCd nominal)"},
    {"step": 8, "category": "voltage", "label": "Set PSU to 8.000 V / 0.1 A",
     "set_voltage_v": 8.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 8.0, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify 8 V accuracy"},
    {"step": 9, "category": "voltage", "label": "Set PSU to 9.000 V / 0.1 A",
     "set_voltage_v": 9.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 9.0, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify 9 V accuracy (NiCd charge limit region)"},
    {"step": 10, "category": "voltage", "label": "Set PSU to 10.000 V / 0.1 A",
     "set_voltage_v": 10.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 10.0, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify 10 V accuracy"},
    {"step": 11, "category": "voltage", "label": "Set PSU to 12.000 V / 0.1 A",
     "set_voltage_v": 12.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 12.0, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify 12 V accuracy"},
    {"step": 12, "category": "voltage", "label": "Set PSU to 14.000 V / 0.1 A",
     "set_voltage_v": 14.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 14.0, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify 14 V accuracy"},
    {"step": 13, "category": "voltage", "label": "Set PSU to 15.500 V / 0.1 A",
     "set_voltage_v": 15.5, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 15.5, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify near-maximum voltage accuracy"},
    {"step": 14, "category": "voltage", "label": "Set PSU to 16.000 V / 0.1 A",
     "set_voltage_v": 16.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 16.0, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify full-scale voltage accuracy"},
    # -- Voltage regulation under load + current accuracy --
    {"step": 15, "category": "regulation", "label": "Set PSU to 7.200 V / 0.500 A",
     "set_voltage_v": 7.2, "set_current_a": 0.5, "measure": "both",
     "expected_value": 7.2, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify regulation at 0.5 A load"},
    {"step": 16, "category": "regulation", "label": "Set PSU to 7.200 V / 1.000 A",
     "set_voltage_v": 7.2, "set_current_a": 1.0, "measure": "both",
     "expected_value": 7.2, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify regulation at 1 A load"},
    {"step": 17, "category": "regulation", "label": "Set PSU to 7.200 V / 2.000 A",
     "set_voltage_v": 7.2, "set_current_a": 2.0, "measure": "both",
     "expected_value": 7.2, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify regulation at 2 A load"},
    {"step": 18, "category": "regulation", "label": "Set PSU to 7.200 V / 4.000 A",
     "set_voltage_v": 7.2, "set_current_a": 4.0, "measure": "both",
     "expected_value": 7.2, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify regulation at 4 A load"},
    {"step": 19, "category": "regulation", "label": "Set PSU to 7.200 V / 6.000 A",
     "set_voltage_v": 7.2, "set_current_a": 6.0, "measure": "both",
     "expected_value": 7.2, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify regulation at 6 A load"},
    {"step": 20, "category": "regulation", "label": "Set PSU to 7.200 V / 8.000 A",
     "set_voltage_v": 7.2, "set_current_a": 8.0, "measure": "both",
     "expected_value": 7.2, "tolerance_pct": 0.05, "tolerance_abs": 0.010,
     "description": "Verify regulation at full 8 A load"},
]

# DC Load Verification Procedure (SDL1030X in 5A/36V range: 0-16V, 0-8A bench range)
# 20 test points: 10 current sink accuracy + 10 voltage readback accuracy
# Current accuracy spec (5A range): ±(0.03% + 0.05% FS) = ±(0.03% + 2.5mA)
# Voltage readback spec (36V range): ±(0.015% + 0.02% FS) = ±(0.015% + 7.2mV)
# Equipment required: 6.5-digit DMM, calibrated DC power supply (SPD1168X)
DC_LOAD_CAL_PROCEDURE = [
    # -- Current sink accuracy (CC mode, PSU at 10V/10A, DMM in series) --
    {"step": 1, "category": "current", "label": "Set Load to 0.010 A CC",
     "set_current_a": 0.010, "source_voltage_v": 10.0, "measure": "current",
     "expected_value": 0.010, "tolerance_pct": 0.03, "tolerance_abs": 0.0025,
     "description": "Verify minimum current sink accuracy (5A range)"},
    {"step": 2, "category": "current", "label": "Set Load to 0.050 A CC",
     "set_current_a": 0.050, "source_voltage_v": 10.0, "measure": "current",
     "expected_value": 0.050, "tolerance_pct": 0.03, "tolerance_abs": 0.0025,
     "description": "Verify 50 mA current sink accuracy"},
    {"step": 3, "category": "current", "label": "Set Load to 0.100 A CC",
     "set_current_a": 0.100, "source_voltage_v": 10.0, "measure": "current",
     "expected_value": 0.100, "tolerance_pct": 0.03, "tolerance_abs": 0.0025,
     "description": "Verify 100 mA current sink accuracy"},
    {"step": 4, "category": "current", "label": "Set Load to 0.250 A CC",
     "set_current_a": 0.250, "source_voltage_v": 10.0, "measure": "current",
     "expected_value": 0.250, "tolerance_pct": 0.03, "tolerance_abs": 0.0025,
     "description": "Verify 250 mA current sink accuracy"},
    {"step": 5, "category": "current", "label": "Set Load to 0.500 A CC",
     "set_current_a": 0.500, "source_voltage_v": 10.0, "measure": "current",
     "expected_value": 0.500, "tolerance_pct": 0.03, "tolerance_abs": 0.0025,
     "description": "Verify 500 mA current sink accuracy"},
    {"step": 6, "category": "current", "label": "Set Load to 1.000 A CC",
     "set_current_a": 1.000, "source_voltage_v": 10.0, "measure": "current",
     "expected_value": 1.000, "tolerance_pct": 0.03, "tolerance_abs": 0.0025,
     "description": "Verify 1 A current sink accuracy"},
    {"step": 7, "category": "current", "label": "Set Load to 2.000 A CC",
     "set_current_a": 2.000, "source_voltage_v": 10.0, "measure": "current",
     "expected_value": 2.000, "tolerance_pct": 0.03, "tolerance_abs": 0.0025,
     "description": "Verify 2 A current sink accuracy"},
    {"step": 8, "category": "current", "label": "Set Load to 3.000 A CC",
     "set_current_a": 3.000, "source_voltage_v": 10.0, "measure": "current",
     "expected_value": 3.000, "tolerance_pct": 0.03, "tolerance_abs": 0.0025,
     "description": "Verify 3 A current sink accuracy"},
    {"step": 9, "category": "current", "label": "Set Load to 4.000 A CC",
     "set_current_a": 4.000, "source_voltage_v": 10.0, "measure": "current",
     "expected_value": 4.000, "tolerance_pct": 0.03, "tolerance_abs": 0.0025,
     "description": "Verify 4 A current sink accuracy"},
    {"step": 10, "category": "current", "label": "Set Load to 5.000 A CC",
     "set_current_a": 5.000, "source_voltage_v": 10.0, "measure": "current",
     "expected_value": 5.000, "tolerance_pct": 0.03, "tolerance_abs": 0.0025,
     "description": "Verify full-range 5 A current sink accuracy (5A range)"},
    # -- Voltage readback accuracy (CV mode, PSU sets voltage, DMM on load terminals) --
    {"step": 11, "category": "voltage", "label": "Verify readback at 0.500 V",
     "source_voltage_v": 0.5, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 0.5, "tolerance_pct": 0.015, "tolerance_abs": 0.0072,
     "description": "Verify voltage readback at 0.5 V (36V range)"},
    {"step": 12, "category": "voltage", "label": "Verify readback at 1.000 V",
     "source_voltage_v": 1.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 1.0, "tolerance_pct": 0.015, "tolerance_abs": 0.0072,
     "description": "Verify voltage readback at 1 V"},
    {"step": 13, "category": "voltage", "label": "Verify readback at 2.000 V",
     "source_voltage_v": 2.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 2.0, "tolerance_pct": 0.015, "tolerance_abs": 0.0072,
     "description": "Verify voltage readback at 2 V"},
    {"step": 14, "category": "voltage", "label": "Verify readback at 4.000 V",
     "source_voltage_v": 4.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 4.0, "tolerance_pct": 0.015, "tolerance_abs": 0.0072,
     "description": "Verify voltage readback at 4 V"},
    {"step": 15, "category": "voltage", "label": "Verify readback at 6.000 V",
     "source_voltage_v": 6.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 6.0, "tolerance_pct": 0.015, "tolerance_abs": 0.0072,
     "description": "Verify voltage readback at 6 V (NiCd nominal)"},
    {"step": 16, "category": "voltage", "label": "Verify readback at 8.000 V",
     "source_voltage_v": 8.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 8.0, "tolerance_pct": 0.015, "tolerance_abs": 0.0072,
     "description": "Verify voltage readback at 8 V"},
    {"step": 17, "category": "voltage", "label": "Verify readback at 10.000 V",
     "source_voltage_v": 10.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 10.0, "tolerance_pct": 0.015, "tolerance_abs": 0.0072,
     "description": "Verify voltage readback at 10 V"},
    {"step": 18, "category": "voltage", "label": "Verify readback at 12.000 V",
     "source_voltage_v": 12.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 12.0, "tolerance_pct": 0.015, "tolerance_abs": 0.0072,
     "description": "Verify voltage readback at 12 V"},
    {"step": 19, "category": "voltage", "label": "Verify readback at 14.000 V",
     "source_voltage_v": 14.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 14.0, "tolerance_pct": 0.015, "tolerance_abs": 0.0072,
     "description": "Verify voltage readback at 14 V"},
    {"step": 20, "category": "voltage", "label": "Verify readback at 16.000 V",
     "source_voltage_v": 16.0, "set_current_a": 0.1, "measure": "voltage",
     "expected_value": 16.0, "tolerance_pct": 0.015, "tolerance_abs": 0.0072,
     "description": "Verify voltage readback at 16 V (PSU full scale)"},
]


# =============================================================================
# FastAPI App
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background station simulator and initialize database"""
    await init_db()
    async with get_db() as db:
        await seed_if_empty(db)
    task = asyncio.create_task(_broadcast_loop())
    yield
    task.cancel()


app = FastAPI(title="Battery Test Bench Mock Server", version="1.4.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _broadcast_loop():
    """Broadcast station updates every second"""
    while True:
        _update_stations()
        # Filter out internal simulation state (keys starting with _)
        broadcast = [{k: v for k, v in s.items() if not k.startswith('_')} for s in _stations.values()]
        data = json.dumps({
            "type": "update",
            "data": broadcast
        })
        disconnected = []
        for ws in _ws_clients:
            try:
                await ws.send_text(data)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            _ws_clients.remove(ws)
        await asyncio.sleep(1.0)


# -- WebSocket --

@app.websocket("/api/ws/live")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    _ws_clients.append(ws)
    try:
        initial = [{k: v for k, v in s.items() if not k.startswith('_')} for s in _stations.values()]
        await ws.send_text(json.dumps({
            "type": "initial",
            "data": initial
        }))
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        if ws in _ws_clients:
            _ws_clients.remove(ws)


# -- Stations --

@app.get("/api/stations")
async def get_stations():
    return list(_stations.values())


@app.get("/api/stations/{station_id}")
async def get_station(station_id: int):
    if station_id not in _stations:
        raise HTTPException(404, "Station not found")
    return _stations[station_id]


class ControlCommand(BaseModel):
    station_id: int
    command: str
    voltage_mv: Optional[int] = None
    current_ma: Optional[int] = None
    voltage_min_mv: Optional[int] = None
    duration_min: Optional[int] = None
    delta_v_enabled: Optional[bool] = None
    delta_v_threshold_mv: Optional[int] = None
    delta_v_peak_hold_time_s: Optional[int] = None
    delta_v_min_charge_time_min: Optional[int] = None


@app.post("/api/stations/control")
async def station_control(cmd: ControlCommand):
    if cmd.station_id not in _stations:
        raise HTTPException(404, "Station not found")
    s = _stations[cmd.station_id]
    if cmd.command == "stop":
        s["state"] = "ready" if s["state"] == "running" else s["state"]
        s["test_phase"] = "idle"
        s["current_ma"] = 0
        s.pop("_charge_sim", None)
        s.pop("delta_v_config", None)
        return {"status": "ok", "message": "Stopped"}
    elif cmd.command == "charge":
        s["state"] = "running"
        s["test_phase"] = "charging"
        s["voltage_mv"] = cmd.voltage_mv or 9000
        s["current_ma"] = cmd.current_ma or 400
        s["elapsed_time_s"] = 0
        # Store -ΔV config for this charge session
        s["delta_v_config"] = {
            "enabled": cmd.delta_v_enabled or False,
            "threshold_mv": cmd.delta_v_threshold_mv or 40,
            "peak_hold_time_s": cmd.delta_v_peak_hold_time_s or 90,
            "min_charge_time_min": cmd.delta_v_min_charge_time_min or 30,
        }
        # Init charge simulation state
        cell_count = s.get("battery_config", {}).get("cell_count", 5)
        start_v = s.get("voltage_mv", 6000)
        s["_charge_sim"] = {
            "start_voltage_mv": start_v,
            "start_temp_c": s.get("temperature_c", 25.0),
            "target_peak_mv": start_v + 1500 + random.randint(0, 300),
            "cell_count": cell_count,
            "tick_count": 0,
        }
        dur = f", duration {cmd.duration_min}min" if cmd.duration_min else ""
        dv = " (-ΔV detection ON)" if s["delta_v_config"]["enabled"] else ""
        return {"status": "ok", "message": f"Charging at {cmd.current_ma}mA, limit {cmd.voltage_mv}mV{dur}{dv}"}
    elif cmd.command == "discharge":
        s["state"] = "running"
        s["test_phase"] = "cap_discharging"
        s["current_ma"] = cmd.current_ma or 460
        s["elapsed_time_s"] = 0
        dur = f", duration {cmd.duration_min}min" if cmd.duration_min else ""
        return {"status": "ok", "message": f"Discharging at {cmd.current_ma}mA, end {cmd.voltage_min_mv}mV{dur}"}
    elif cmd.command == "wait":
        s["state"] = "running"
        s["test_phase"] = "post_charge_rest"
        s["current_ma"] = 0
        s["elapsed_time_s"] = 0
        return {"status": "ok", "message": f"Waiting {cmd.duration_min or 60}min"}
    return {"status": "error", "message": f"Unknown command: {cmd.command}"}


@app.get("/api/stations/{station_id}/eeprom")
async def read_eeprom(station_id: int):
    if station_id not in _stations:
        raise HTTPException(404, "Station not found")
    return _stations[station_id].get("battery_config")


@app.post("/api/stations/{station_id}/stop")
async def stop_station(station_id: int):
    if station_id in _stations:
        _stations[station_id]["state"] = "ready"
        _stations[station_id]["test_phase"] = "idle"
    return {"status": "ok"}


@app.post("/api/stations/{station_id}/reset")
async def reset_station(station_id: int):
    if station_id in _stations:
        _stations[station_id]["state"] = "empty"
        _stations[station_id]["error_message"] = None
    return {"status": "ok"}


# -- Diagnostic Connection Check --

# Simulated hardware per station
_STATION_HARDWARE = {}

def _get_station_hardware(station_id: int) -> dict:
    """Generate deterministic mock hardware config per station"""
    if station_id not in _STATION_HARDWARE:
        psu_models = [
            ("TDK-Lambda Z+ 20-20", "1.23"), ("TDK-Lambda Z+ 20-20", "1.24"),
            ("TDK-Lambda Z+ 36-12", "1.23"), ("TDK-Lambda Z+ 60-7", "2.01"),
        ]
        load_models = [
            ("BK Precision 8500", "2.01"), ("BK Precision 8502", "1.15"),
            ("BK Precision 8500", "2.03"), ("BK Precision 8514", "1.08"),
        ]
        psu = psu_models[(station_id - 1) % len(psu_models)]
        load = load_models[(station_id - 1) % len(load_models)]
        _STATION_HARDWARE[station_id] = {"psu": psu, "load": load}
    return _STATION_HARDWARE[station_id]


@app.get("/api/stations/{station_id}/diagnostics")
async def station_diagnostics(station_id: int):
    """Run diagnostic connection check on station PSU, DC load, temp sensor, and EEPROM"""
    if station_id not in _stations:
        raise HTTPException(404, "Station not found")

    s = _stations[station_id]
    hw = _get_station_hardware(station_id)
    is_empty = s["state"] == "empty"
    is_error = s["state"] == "error"

    # Simulate SCPI *IDN? response times (ms)
    psu_resp = random.randint(5, 25)
    load_resp = random.randint(5, 25)

    # PSU diagnostics
    psu_ok = not is_error or station_id != 11  # Station 11 has error
    psu_model, psu_fw = hw["psu"]
    psu_diag = {
        "connected": psu_ok,
        "model": psu_model if psu_ok else None,
        "firmware": psu_fw if psu_ok else None,
        "serial_number": f"PSU-{station_id:03d}-{2024 + station_id % 3}" if psu_ok else None,
        "response_time_ms": psu_resp if psu_ok else None,
        "scpi_idn": f"{psu_model},SN-{station_id:03d},{psu_fw}" if psu_ok else "No response",
        "status": "ok" if psu_ok else "no_response",
        "voltage_readback_mv": s["voltage_mv"] if psu_ok and s["voltage_mv"] else 0,
        "current_readback_ma": s["current_ma"] if psu_ok and s["current_ma"] else 0,
        "output_enabled": s["state"] == "running",
    }

    # DC Electronic Load diagnostics
    load_ok = not is_error or station_id != 11
    load_model, load_fw = hw["load"]
    load_diag = {
        "connected": load_ok,
        "model": load_model if load_ok else None,
        "firmware": load_fw if load_ok else None,
        "serial_number": f"LOAD-{station_id:03d}-{2024 + station_id % 2}" if load_ok else None,
        "response_time_ms": load_resp if load_ok else None,
        "scpi_idn": f"{load_model},SN-{station_id:03d},{load_fw}" if load_ok else "No response",
        "status": "ok" if load_ok else "no_response",
        "mode": "CC" if load_ok else None,
        "input_enabled": s["state"] == "running" and s["test_phase"] in ("cap_discharging", "pre_discharge", "fast_discharging"),
    }

    # Temperature sensor diagnostics
    temp_ok = s["temperature_valid"] if not is_empty else False
    temp_diag = {
        "connected": temp_ok,
        "reading_c": s["temperature_c"] if temp_ok else None,
        "status": "ok" if temp_ok else ("not_detected" if is_empty else "sensor_fault"),
    }

    # EEPROM diagnostics
    eeprom_ok = s["eeprom_present"]
    eeprom_diag = {
        "detected": eeprom_ok,
        "part_number": s["battery_config"]["part_number"] if eeprom_ok and s["battery_config"] else None,
        "amendment": s["battery_config"]["amendment"] if eeprom_ok and s["battery_config"] else None,
        "status": "ok" if eeprom_ok else "no_eeprom",
    }

    all_ok = psu_ok and load_ok and temp_ok and eeprom_ok
    return {
        "station_id": station_id,
        "timestamp": datetime.now().isoformat(),
        "psu": psu_diag,
        "dc_load": load_diag,
        "temperature_sensor": temp_diag,
        "eeprom": eeprom_diag,
        "overall": "ok" if all_ok else "warning" if (psu_ok and load_ok) else "error",
    }


# -- Task Log (per-station manual task history) --

@app.get("/api/stations/{station_id}/task-log")
async def get_task_log(station_id: int):
    async with get_db() as db:
        logs = await execute_all(db, "SELECT * FROM task_logs WHERE station_id = ?", (station_id,))
        for l in logs:
            l["params"] = from_json(l["params"]) or {}
            l["chart_data"] = from_json(l["chart_data"]) or []
        return logs


@app.post("/api/stations/{station_id}/task-log")
async def save_task_log(station_id: int, data: dict):
    async with get_db() as db:
        log_id = await execute_insert(db,
            """INSERT INTO task_logs (station_id, type, params, start_time, end_time,
               chart_data, data_points, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (station_id, data.get("type", "unknown"), json_col(data.get("params", {})),
             data.get("startTime"), data.get("endTime"),
             json_col(data.get("chartData", [])), len(data.get("chartData", [])),
             data.get("status", "completed")))
        entry = await execute_one(db, "SELECT * FROM task_logs WHERE id = ?", (log_id,))
        entry["params"] = from_json(entry["params"]) or {}
        entry["chart_data"] = from_json(entry["chart_data"]) or []
        return entry


# -- Customers (Full CRUD) --

@app.get("/api/customers")
async def get_customers(search: str = ""):
    async with get_db() as db:
        if search:
            q = f"%{search}%"
            return await execute_all(db,
                "SELECT * FROM customers WHERE name LIKE ? OR customer_code LIKE ? OR contact_person LIKE ?",
                (q, q, q))
        return await execute_all(db, "SELECT * FROM customers")


@app.get("/api/customers/{customer_id}")
async def get_customer(customer_id: int):
    async with get_db() as db:
        c = await execute_one(db, "SELECT * FROM customers WHERE id = ?", (customer_id,))
        if not c:
            raise HTTPException(404, "Customer not found")
        wo_count = await execute_one(db,
            "SELECT COUNT(*) as cnt FROM work_orders WHERE customer_id = ?", (customer_id,))
        c["total_work_orders"] = wo_count["cnt"] if wo_count else 0
        return c


@app.post("/api/customers")
async def create_customer(data: dict):
    async with get_db() as db:
        code = data.get("customer_code") or (data.get("name", "NEW")[:3].upper() + "001")
        new_id = await execute_insert(db,
            """INSERT INTO customers (name, customer_code, contact_person, email, phone,
               address_line1, notes, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.get("name"), code, data.get("contact_person"), data.get("email"),
             data.get("phone"), data.get("address_line1") or data.get("address"),
             data.get("notes"), data.get("is_active", True)))
        return await execute_one(db, "SELECT * FROM customers WHERE id = ?", (new_id,))


@app.put("/api/customers/{customer_id}")
async def update_customer(customer_id: int, data: dict):
    async with get_db() as db:
        existing = await execute_one(db, "SELECT * FROM customers WHERE id = ?", (customer_id,))
        if not existing:
            raise HTTPException(404, "Customer not found")
        fields = {k: v for k, v in data.items() if k != "id"}
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            await execute_update(db,
                f"UPDATE customers SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (*fields.values(), customer_id))
        return await execute_one(db, "SELECT * FROM customers WHERE id = ?", (customer_id,))


@app.delete("/api/customers/{customer_id}")
async def delete_customer(customer_id: int):
    async with get_db() as db:
        rows = await execute_update(db, "DELETE FROM customers WHERE id = ?", (customer_id,))
        if rows == 0:
            raise HTTPException(404, "Customer not found")
        return {"status": "ok"}


# -- Work Orders (Full CRUD) --

@app.get("/api/work-orders")
async def get_work_orders(status: str = "", search: str = ""):
    async with get_db() as db:
        base = """SELECT wo.*, c.name as customer_name FROM work_orders wo
                  LEFT JOIN customers c ON wo.customer_id = c.id"""
        conditions = []
        params = []
        if status:
            conditions.append("wo.status = ?")
            params.append(status)
        if search:
            q = f"%{search}%"
            conditions.append("(wo.work_order_number LIKE ? OR wo.customer_reference LIKE ? OR c.name LIKE ?)")
            params.extend([q, q, q])
        if conditions:
            base += " WHERE " + " AND ".join(conditions)
        orders = await execute_all(db, base, params)
        for wo in orders:
            items = await execute_all(db,
                "SELECT * FROM work_order_items WHERE work_order_id = ?", (wo["id"],))
            wo["items"] = items
            wo["battery_count"] = len(items)
        return orders


@app.get("/api/work-orders/{wo_id}")
async def get_work_order(wo_id: int):
    async with get_db() as db:
        wo = await execute_one(db,
            """SELECT wo.*, c.name as customer_name FROM work_orders wo
               LEFT JOIN customers c ON wo.customer_id = c.id
               WHERE wo.id = ?""", (wo_id,))
        if not wo:
            raise HTTPException(404, "Work order not found")
        items = await execute_all(db,
            "SELECT * FROM work_order_items WHERE work_order_id = ?", (wo_id,))
        wo["items"] = items
        wo["battery_count"] = len(items)
        return wo


@app.post("/api/work-orders")
async def create_work_order(data: dict):
    async with get_db() as db:
        # Generate WO number
        max_row = await execute_one(db, "SELECT MAX(id) as maxid FROM work_orders")
        next_num = (max_row["maxid"] or 0) + 1
        wo_number = f"OT-2026-{next_num:04d}"

        wo_id = await execute_insert(db,
            """INSERT INTO work_orders (work_order_number, customer_reference, customer_id,
               service_type, priority, status, received_date, assigned_technician, customer_notes)
            VALUES (?, ?, ?, ?, ?, 'received', ?, '', ?)""",
            (wo_number, data.get("customer_reference", ""), data.get("customer_id"),
             data.get("service_type", "capacity_test"), data.get("priority", "normal"),
             datetime.now().isoformat(), data.get("customer_notes", "")))

        items = []
        for bat in data.get("batteries", []):
            item_id = await execute_insert(db,
                """INSERT INTO work_order_items (work_order_id, serial_number, part_number,
                   revision, amendment, reported_condition, status)
                VALUES (?, ?, ?, ?, ?, ?, 'queued')""",
                (wo_id, bat.get("serial_number", ""), bat.get("part_number", ""),
                 bat.get("revision", ""), bat.get("amendment", ""),
                 bat.get("reported_condition", "")))
            items.append({"id": item_id, **bat, "status": "queued", "station_id": None, "result": None})

        wo = await execute_one(db, "SELECT * FROM work_orders WHERE id = ?", (wo_id,))
        cust = await execute_one(db, "SELECT name FROM customers WHERE id = ?", (data.get("customer_id"),))
        wo["customer_name"] = cust["name"] if cust else ""
        wo["items"] = items
        wo["battery_count"] = len(items)
        return {"status": "ok", "message": f"Work order {wo_number} created with {len(items)} batteries", "work_order": wo}


@app.put("/api/work-orders/{wo_id}")
async def update_work_order(wo_id: int, data: dict):
    async with get_db() as db:
        existing = await execute_one(db, "SELECT * FROM work_orders WHERE id = ?", (wo_id,))
        if not existing:
            raise HTTPException(404, "Work order not found")
        fields = {k: v for k, v in data.items() if k not in ("id", "items", "customer_name", "battery_count")}
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            await execute_update(db,
                f"UPDATE work_orders SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (*fields.values(), wo_id))
        wo = await execute_one(db,
            """SELECT wo.*, c.name as customer_name FROM work_orders wo
               LEFT JOIN customers c ON wo.customer_id = c.id
               WHERE wo.id = ?""", (wo_id,))
        items = await execute_all(db,
            "SELECT * FROM work_order_items WHERE work_order_id = ?", (wo_id,))
        wo["items"] = items
        wo["battery_count"] = len(items)
        return wo


@app.delete("/api/work-orders/{wo_id}")
async def delete_work_order(wo_id: int):
    async with get_db() as db:
        rows = await execute_update(db, "DELETE FROM work_orders WHERE id = ?", (wo_id,))
        if rows == 0:
            raise HTTPException(404, "Work order not found")
        return {"status": "ok"}


@app.post("/api/work-orders/{wo_id}/items/{item_id}/assign")
async def assign_battery_to_station(wo_id: int, item_id: int, data: dict):
    """Assign a battery from a work order to a test station"""
    station_id = data.get("station_id")
    if not station_id or station_id not in _stations:
        raise HTTPException(400, "Invalid station ID")
    async with get_db() as db:
        item = await execute_one(db,
            "SELECT * FROM work_order_items WHERE id = ? AND work_order_id = ?", (item_id, wo_id))
        if not item:
            raise HTTPException(404, "Item not found")
        await execute_update(db,
            "UPDATE work_order_items SET status = 'testing', current_station_id = ? WHERE id = ?",
            (station_id, item_id))
        # Update in-memory station
        s = _stations[station_id]
        s["state"] = "ready"
        s["work_order_item_id"] = item_id
        return {"status": "ok", "message": f"Battery {item['serial_number']} assigned to station {station_id}"}


# -- Battery Profiles (Full CRUD) --

@app.get("/api/battery-profiles")
async def get_battery_profiles():
    async with get_db() as db:
        return await execute_all(db, "SELECT * FROM battery_profiles")


@app.get("/api/battery-profiles/{profile_id}")
async def get_battery_profile(profile_id: int):
    async with get_db() as db:
        p = await execute_one(db, "SELECT * FROM battery_profiles WHERE id = ?", (profile_id,))
        if not p:
            raise HTTPException(404, "Profile not found")
        return p


@app.post("/api/battery-profiles")
async def create_battery_profile(data: dict):
    async with get_db() as db:
        fields = {k: v for k, v in data.items() if k != "id"}
        fields.setdefault("is_active", True)
        columns = ", ".join(fields.keys())
        placeholders = ", ".join("?" for _ in fields)
        new_id = await execute_insert(db,
            f"INSERT INTO battery_profiles ({columns}) VALUES ({placeholders})",
            tuple(fields.values()))
        return await execute_one(db, "SELECT * FROM battery_profiles WHERE id = ?", (new_id,))


@app.put("/api/battery-profiles/{profile_id}")
async def update_battery_profile(profile_id: int, data: dict):
    async with get_db() as db:
        existing = await execute_one(db, "SELECT * FROM battery_profiles WHERE id = ?", (profile_id,))
        if not existing:
            raise HTTPException(404, "Profile not found")
        fields = {k: v for k, v in data.items() if k != "id"}
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            await execute_update(db,
                f"UPDATE battery_profiles SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (*fields.values(), profile_id))
        return await execute_one(db, "SELECT * FROM battery_profiles WHERE id = ?", (profile_id,))


@app.delete("/api/battery-profiles/{profile_id}")
async def delete_battery_profile(profile_id: int):
    async with get_db() as db:
        rows = await execute_update(db, "DELETE FROM battery_profiles WHERE id = ?", (profile_id,))
        if rows == 0:
            raise HTTPException(404, "Profile not found")
        return {"status": "ok"}


# -- Tech Pubs (Component Maintenance Manuals) --

@app.get("/api/tech-pubs")
async def get_tech_pubs():
    async with get_db() as db:
        pubs = await execute_all(db, "SELECT * FROM tech_pubs")
        for tp in pubs:
            tp["applicable_part_numbers"] = from_json(tp["applicable_part_numbers"]) or []
        return pubs


@app.get("/api/tech-pubs/match/{part_number}")
async def match_tech_pub(part_number: str):
    """Auto-match a battery P/N to its applicable tech pub"""
    async with get_db() as db:
        # Search JSON array for part number
        tp = await execute_one(db,
            "SELECT * FROM tech_pubs WHERE applicable_part_numbers LIKE ?",
            (f'%"{part_number}"%',))
        if not tp:
            raise HTTPException(404, f"No tech pub found for P/N {part_number}")
        tp["applicable_part_numbers"] = from_json(tp["applicable_part_numbers"])
        recipes = await execute_all(db,
            "SELECT * FROM recipes WHERE tech_pub_id = ? AND is_active = 1", (tp["id"],))
        for r in recipes:
            r["steps"] = from_json(r["steps"])
            r["applicable_part_numbers"] = from_json(r["applicable_part_numbers"])
        return {**tp, "recipes": recipes}


@app.get("/api/tech-pubs/{tech_pub_id}")
async def get_tech_pub(tech_pub_id: int):
    async with get_db() as db:
        tp = await execute_one(db, "SELECT * FROM tech_pubs WHERE id = ?", (tech_pub_id,))
        if not tp:
            raise HTTPException(404, "Tech pub not found")
        tp["applicable_part_numbers"] = from_json(tp["applicable_part_numbers"]) or []
        # Include linked recipes
        recipes = await execute_all(db, "SELECT * FROM recipes WHERE tech_pub_id = ?", (tech_pub_id,))
        for r in recipes:
            r["steps"] = from_json(r["steps"])
            r["applicable_part_numbers"] = from_json(r["applicable_part_numbers"])
        return {**tp, "recipes": recipes}


@app.post("/api/tech-pubs")
async def create_tech_pub(data: dict):
    async with get_db() as db:
        apn = json_col(data.get("applicable_part_numbers", []))
        new_id = await execute_insert(db,
            """INSERT INTO tech_pubs (cmm_number, title, revision, revision_date,
               applicable_part_numbers, ata_chapter, issued_by, notes, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.get("cmm_number"), data.get("title"), data.get("revision"),
             data.get("revision_date"), apn, data.get("ata_chapter"),
             data.get("issued_by"), data.get("notes"), data.get("is_active", True)))
        tp = await execute_one(db, "SELECT * FROM tech_pubs WHERE id = ?", (new_id,))
        tp["applicable_part_numbers"] = from_json(tp["applicable_part_numbers"]) or []
        return tp


@app.put("/api/tech-pubs/{tech_pub_id}")
async def update_tech_pub(tech_pub_id: int, data: dict):
    async with get_db() as db:
        existing = await execute_one(db, "SELECT * FROM tech_pubs WHERE id = ?", (tech_pub_id,))
        if not existing:
            raise HTTPException(404, "Tech pub not found")
        fields = {k: v for k, v in data.items() if k != "id"}
        if "applicable_part_numbers" in fields:
            fields["applicable_part_numbers"] = json_col(fields["applicable_part_numbers"])
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            await execute_update(db,
                f"UPDATE tech_pubs SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (*fields.values(), tech_pub_id))
        tp = await execute_one(db, "SELECT * FROM tech_pubs WHERE id = ?", (tech_pub_id,))
        tp["applicable_part_numbers"] = from_json(tp["applicable_part_numbers"]) or []
        return tp


@app.delete("/api/tech-pubs/{tech_pub_id}")
async def delete_tech_pub(tech_pub_id: int):
    async with get_db() as db:
        rows = await execute_update(db, "DELETE FROM tech_pubs WHERE id = ?", (tech_pub_id,))
        if rows == 0:
            raise HTTPException(404, "Tech pub not found")
        return {"status": "ok"}


# -- Recipes (Reworked - linked to Tech Pubs) --

@app.get("/api/recipes")
async def get_recipes(tech_pub_id: int = 0, part_number: str = ""):
    async with get_db() as db:
        base = "SELECT * FROM recipes"
        conditions = []
        params = []
        if tech_pub_id:
            conditions.append("tech_pub_id = ?")
            params.append(tech_pub_id)
        if part_number:
            conditions.append("applicable_part_numbers LIKE ?")
            params.append(f'%"{part_number}"%')
        if conditions:
            base += " WHERE " + " AND ".join(conditions)
        recipes = await execute_all(db, base, params)
        for r in recipes:
            r["steps"] = from_json(r["steps"]) or []
            r["applicable_part_numbers"] = from_json(r["applicable_part_numbers"]) or []
        return recipes


@app.get("/api/recipes/{recipe_id}")
async def get_recipe(recipe_id: int):
    async with get_db() as db:
        r = await execute_one(db, "SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        if not r:
            raise HTTPException(404, "Recipe not found")
        r["steps"] = from_json(r["steps"]) or []
        r["applicable_part_numbers"] = from_json(r["applicable_part_numbers"]) or []
        return r


@app.post("/api/recipes")
async def create_recipe(data: dict):
    async with get_db() as db:
        new_id = await execute_insert(db,
            """INSERT INTO recipes (tech_pub_id, cmm_reference, name, description,
               recipe_type, is_default, applicable_part_numbers, steps, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.get("tech_pub_id"), data.get("cmm_reference"), data.get("name"),
             data.get("description"), data.get("recipe_type"), data.get("is_default", False),
             json_col(data.get("applicable_part_numbers", [])),
             json_col(data.get("steps", [])), data.get("is_active", True)))
        r = await execute_one(db, "SELECT * FROM recipes WHERE id = ?", (new_id,))
        r["steps"] = from_json(r["steps"]) or []
        r["applicable_part_numbers"] = from_json(r["applicable_part_numbers"]) or []
        return r


@app.put("/api/recipes/{recipe_id}")
async def update_recipe(recipe_id: int, data: dict):
    async with get_db() as db:
        existing = await execute_one(db, "SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        if not existing:
            raise HTTPException(404, "Recipe not found")
        fields = {k: v for k, v in data.items() if k != "id"}
        if "steps" in fields:
            fields["steps"] = json_col(fields["steps"])
        if "applicable_part_numbers" in fields:
            fields["applicable_part_numbers"] = json_col(fields["applicable_part_numbers"])
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            await execute_update(db,
                f"UPDATE recipes SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (*fields.values(), recipe_id))
        r = await execute_one(db, "SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        r["steps"] = from_json(r["steps"]) or []
        r["applicable_part_numbers"] = from_json(r["applicable_part_numbers"]) or []
        return r


@app.delete("/api/recipes/{recipe_id}")
async def delete_recipe(recipe_id: int):
    async with get_db() as db:
        rows = await execute_update(db, "DELETE FROM recipes WHERE id = ?", (recipe_id,))
        if rows == 0:
            raise HTTPException(404, "Recipe not found")
        return {"status": "ok"}


# -- Calibrated Tools --

@app.get("/api/tools")
async def get_tools(category: str = ""):
    async with get_db() as db:
        if category:
            results = await execute_all(db,
                "SELECT * FROM tools WHERE is_active = 1 AND category = ?", (category,))
        else:
            results = await execute_all(db, "SELECT * FROM tools WHERE is_active = 1")
        # Add computed validity status
        today = datetime.now().strftime("%Y-%m-%d")
        for t in results:
            t["is_valid"] = t.get("valid_until", "") >= today
            days_left = (datetime.strptime(t["valid_until"], "%Y-%m-%d") - datetime.now()).days if t.get("valid_until") else 0
            t["days_until_expiry"] = max(0, days_left)
            t["validity_status"] = "valid" if days_left > 30 else ("expiring_soon" if days_left > 0 else "expired")
        return results


@app.get("/api/tools/valid")
async def get_valid_tools(category: str = ""):
    """Only return tools within calibration validity"""
    async with get_db() as db:
        today = datetime.now().strftime("%Y-%m-%d")
        if category:
            return await execute_all(db,
                "SELECT * FROM tools WHERE is_active = 1 AND valid_until >= ? AND category = ?",
                (today, category))
        return await execute_all(db,
            "SELECT * FROM tools WHERE is_active = 1 AND valid_until >= ?", (today,))


@app.get("/api/tools/{tool_id}")
async def get_tool(tool_id: int):
    async with get_db() as db:
        t = await execute_one(db, "SELECT * FROM tools WHERE id = ?", (tool_id,))
        if not t:
            raise HTTPException(404, "Tool not found")
        return t


@app.post("/api/tools")
async def create_tool(data: dict):
    async with get_db() as db:
        fields = {k: v for k, v in data.items() if k != "id"}
        fields.setdefault("is_active", True)
        columns = ", ".join(fields.keys())
        placeholders = ", ".join("?" for _ in fields)
        new_id = await execute_insert(db,
            f"INSERT INTO tools ({columns}) VALUES ({placeholders})",
            tuple(fields.values()))
        return await execute_one(db, "SELECT * FROM tools WHERE id = ?", (new_id,))


@app.put("/api/tools/{tool_id}")
async def update_tool(tool_id: int, data: dict):
    async with get_db() as db:
        existing = await execute_one(db, "SELECT * FROM tools WHERE id = ?", (tool_id,))
        if not existing:
            raise HTTPException(404, "Tool not found")
        fields = {k: v for k, v in data.items() if k != "id"}
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            await execute_update(db,
                f"UPDATE tools SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (*fields.values(), tool_id))
        return await execute_one(db, "SELECT * FROM tools WHERE id = ?", (tool_id,))


@app.delete("/api/tools/{tool_id}")
async def delete_tool(tool_id: int):
    async with get_db() as db:
        rows = await execute_update(db, "DELETE FROM tools WHERE id = ?", (tool_id,))
        if rows == 0:
            raise HTTPException(404, "Tool not found")
        return {"status": "ok"}


# -- Station Calibration (internal PSU + DC Load) --

@app.get("/api/station-calibration")
async def get_station_calibrations():
    async with get_db() as db:
        rows = await execute_all(db, "SELECT * FROM station_calibrations ORDER BY station_id, unit")
        today = datetime.now().strftime("%Y-%m-%d")
        grouped = {}
        for row in rows:
            sid = row["station_id"]
            if sid not in grouped:
                grouped[sid] = {"station_id": sid, "psu": {}, "dc_load": {}}
            unit_data = {
                "model": row["model"], "serial_number": row["serial_number"],
                "last_calibration_date": row["last_calibration_date"],
                "next_due_date": row["next_due_date"],
                "calibrated_by": row["calibrated_by"],
                "calibration_certificate": row["calibration_certificate"],
                "result": row["result"],
                "readings": from_json(row["readings"]) or [],
            }
            due = row["next_due_date"]
            if not due:
                unit_data["validity_status"] = "uncalibrated"
            elif due < today:
                unit_data["validity_status"] = "overdue"
            else:
                days_left = (datetime.strptime(due, "%Y-%m-%d") - datetime.now()).days
                unit_data["validity_status"] = "expiring_soon" if days_left <= 30 else "valid"
            grouped[sid][row["unit"]] = unit_data
        return list(grouped.values())


@app.get("/api/station-calibration/{station_id}")
async def get_station_calibration(station_id: int):
    async with get_db() as db:
        rows = await execute_all(db,
            "SELECT * FROM station_calibrations WHERE station_id = ? ORDER BY unit",
            (station_id,))
        if not rows:
            raise HTTPException(404, "Station calibration not found")
        today = datetime.now().strftime("%Y-%m-%d")
        result = {"station_id": station_id, "psu": {}, "dc_load": {}}
        for row in rows:
            unit_data = {
                "model": row["model"], "serial_number": row["serial_number"],
                "last_calibration_date": row["last_calibration_date"],
                "next_due_date": row["next_due_date"],
                "calibrated_by": row["calibrated_by"],
                "calibration_certificate": row["calibration_certificate"],
                "result": row["result"],
                "readings": from_json(row["readings"]) or [],
            }
            due = row["next_due_date"]
            if not due:
                unit_data["validity_status"] = "uncalibrated"
            elif due < today:
                unit_data["validity_status"] = "overdue"
            else:
                days_left = (datetime.strptime(due, "%Y-%m-%d") - datetime.now()).days
                unit_data["validity_status"] = "expiring_soon" if days_left <= 30 else "valid"
            result[row["unit"]] = unit_data
        return result


@app.get("/api/station-calibration/procedures/psu")
async def get_psu_procedure():
    return PSU_CAL_PROCEDURE


@app.get("/api/station-calibration/procedures/dc-load")
async def get_dc_load_procedure():
    return DC_LOAD_CAL_PROCEDURE


@app.put("/api/station-calibration/{station_id}/{unit}")
async def update_station_calibration(station_id: int, unit: str, data: dict):
    """Update PSU or DC Load calibration for a station (unit = 'psu' or 'dc_load')"""
    if unit not in ("psu", "dc_load"):
        raise HTTPException(400, "Unit must be 'psu' or 'dc_load'")
    async with get_db() as db:
        readings = json_col(data.pop("readings", None)) if "readings" in data else None
        fields = {k: v for k, v in data.items() if k not in ("station_id", "unit")}
        if readings:
            fields["readings"] = readings
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            await execute_update(db,
                f"UPDATE station_calibrations SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE station_id = ? AND unit = ?",
                (*fields.values(), station_id, unit))
        return await execute_one(db,
            "SELECT * FROM station_calibrations WHERE station_id = ? AND unit = ?",
            (station_id, unit))


# -- Work Jobs --

@app.get("/api/work-jobs")
async def get_work_jobs(work_order_id: int = 0, station_id: int = 0, status: str = ""):
    async with get_db() as db:
        base = "SELECT * FROM work_jobs"
        conditions = []
        params = []
        if work_order_id:
            conditions.append("work_order_id = ?")
            params.append(work_order_id)
        if station_id:
            conditions.append("station_id = ?")
            params.append(station_id)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if conditions:
            base += " WHERE " + " AND ".join(conditions)
        jobs = await execute_all(db, base, params)
        for j in jobs:
            tasks = await execute_all(db,
                "SELECT * FROM work_job_tasks WHERE work_job_id = ? ORDER BY task_number", (j["id"],))
            for t in tasks:
                t["params"] = from_json(t["params"]) or {}
                t["tools_used"] = from_json(t["tools_used"]) or []
                t["measured_values"] = from_json(t["measured_values"]) or {}
                t["chart_data"] = from_json(t["chart_data"]) or []
            j["tasks"] = tasks
        return jobs


@app.get("/api/work-jobs/{job_id}")
async def get_work_job(job_id: int):
    async with get_db() as db:
        j = await execute_one(db, "SELECT * FROM work_jobs WHERE id = ?", (job_id,))
        if not j:
            raise HTTPException(404, "Work job not found")
        tasks = await execute_all(db,
            "SELECT * FROM work_job_tasks WHERE work_job_id = ? ORDER BY task_number", (job_id,))
        for t in tasks:
            t["params"] = from_json(t["params"]) or {}
            t["tools_used"] = from_json(t["tools_used"]) or []
            t["measured_values"] = from_json(t["measured_values"]) or {}
            t["chart_data"] = from_json(t["chart_data"]) or []
        j["tasks"] = tasks
        return j


@app.post("/api/work-jobs")
async def create_work_job(data: dict):
    station_id = data.get("station_id")
    if not station_id or station_id not in _stations:
        raise HTTPException(400, "Invalid station ID")
    async with get_db() as db:
        job_id = await execute_insert(db,
            """INSERT INTO work_jobs (work_order_id, work_order_item_id, work_order_number,
               battery_serial, battery_part_number, battery_amendment, tech_pub_id,
               tech_pub_cmm, tech_pub_revision, recipe_id, recipe_name, recipe_cmm_ref,
               station_id, status, started_at, started_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?, ?)""",
            (data.get("work_order_id"), data.get("work_order_item_id"),
             data.get("work_order_number", ""), data.get("battery_serial", ""),
             data.get("battery_part_number", ""), data.get("battery_amendment", ""),
             data.get("tech_pub_id"), data.get("tech_pub_cmm", ""),
             data.get("tech_pub_revision", ""), data.get("recipe_id"),
             data.get("recipe_name", ""), data.get("recipe_cmm_ref", ""),
             station_id, datetime.now().isoformat(), data.get("started_by", "")))

        # Update in-memory station
        s = _stations[station_id]
        s["state"] = "ready"
        s["work_job_id"] = job_id
        s["work_order_item_id"] = data.get("work_order_item_id")

        # Update WO item status in DB
        wo_id = data.get("work_order_id")
        item_id = data.get("work_order_item_id")
        if wo_id and item_id:
            await execute_update(db,
                "UPDATE work_order_items SET status = 'testing', current_station_id = ? WHERE id = ?",
                (station_id, item_id))

        job = await execute_one(db, "SELECT * FROM work_jobs WHERE id = ?", (job_id,))
        job["tasks"] = []
        return job


@app.put("/api/work-jobs/{job_id}")
async def update_work_job(job_id: int, data: dict):
    async with get_db() as db:
        j = await execute_one(db, "SELECT * FROM work_jobs WHERE id = ?", (job_id,))
        if not j:
            raise HTTPException(404, "Work job not found")
        fields = {k: v for k, v in data.items() if k not in ("id", "tasks")}
        if data.get("status") == "completed":
            fields["completed_at"] = datetime.now().isoformat()
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            await execute_update(db,
                f"UPDATE work_jobs SET {set_clause} WHERE id = ?",
                (*fields.values(), job_id))

        if data.get("status") == "completed":
            station_id = j["station_id"]
            if station_id and station_id in _stations:
                _stations[station_id]["work_job_id"] = None
                _stations[station_id]["state"] = "ready"
            result = data.get("result")
            if j["work_order_id"] and j["work_order_item_id"] and result:
                await execute_update(db,
                    "UPDATE work_order_items SET status = 'completed', result = ?, current_station_id = NULL WHERE id = ?",
                    (result, j["work_order_item_id"]))

        updated = await execute_one(db, "SELECT * FROM work_jobs WHERE id = ?", (job_id,))
        tasks = await execute_all(db,
            "SELECT * FROM work_job_tasks WHERE work_job_id = ? ORDER BY task_number", (job_id,))
        for t in tasks:
            t["params"] = from_json(t["params"]) or {}
            t["tools_used"] = from_json(t["tools_used"]) or []
            t["measured_values"] = from_json(t["measured_values"]) or {}
            t["chart_data"] = from_json(t["chart_data"]) or []
        updated["tasks"] = tasks
        return updated


@app.post("/api/work-jobs/{job_id}/tasks")
async def append_task(job_id: int, data: dict):
    """Append an immutable task record to a work job"""
    async with get_db() as db:
        j = await execute_one(db, "SELECT id FROM work_jobs WHERE id = ?", (job_id,))
        if not j:
            raise HTTPException(404, "Work job not found")
        count = await execute_one(db,
            "SELECT COUNT(*) as cnt FROM work_job_tasks WHERE work_job_id = ?", (job_id,))
        task_number = (count["cnt"] if count else 0) + 1

        task_id = await execute_insert(db,
            """INSERT INTO work_job_tasks
               (work_job_id, task_number, step_number, type, label, params, source,
                tools_used, measured_values, step_result, start_time, end_time,
                chart_data, data_points, status, result_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job_id, task_number, data.get("step_number"), data.get("type", "unknown"),
             data.get("label", ""), json_col(data.get("params", {})),
             data.get("source", "manual"), json_col(data.get("tools_used", [])),
             json_col(data.get("measured_values", {})), data.get("step_result"),
             data.get("start_time", datetime.now().isoformat()), data.get("end_time"),
             json_col(data.get("chart_data", [])), len(data.get("chart_data", [])),
             data.get("status", "running"), data.get("result_notes", "")))

        task = await execute_one(db, "SELECT * FROM work_job_tasks WHERE id = ?", (task_id,))
        task["params"] = from_json(task["params"]) or {}
        task["tools_used"] = from_json(task["tools_used"]) or []
        task["measured_values"] = from_json(task["measured_values"]) or {}
        task["chart_data"] = from_json(task["chart_data"]) or []
        return task


@app.put("/api/work-jobs/{job_id}/tasks/{task_id}")
async def update_task(job_id: int, task_id: int, data: dict):
    """Update a running task (end_time, chart_data, status only)"""
    async with get_db() as db:
        task = await execute_one(db,
            "SELECT * FROM work_job_tasks WHERE id = ? AND work_job_id = ?", (task_id, job_id))
        if not task:
            raise HTTPException(404, "Task not found")
        fields = {}
        if "end_time" in data:
            fields["end_time"] = data["end_time"]
        if "chart_data" in data:
            fields["chart_data"] = json_col(data["chart_data"])
            fields["data_points"] = len(data["chart_data"])
        if "status" in data:
            fields["status"] = data["status"]
        if "tools_used" in data:
            fields["tools_used"] = json_col(data["tools_used"])
        if "measured_values" in data:
            fields["measured_values"] = json_col(data["measured_values"])
        if "step_result" in data:
            fields["step_result"] = data["step_result"]
        if "result_notes" in data:
            fields["result_notes"] = data["result_notes"]
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            await execute_update(db,
                f"UPDATE work_job_tasks SET {set_clause} WHERE id = ?",
                (*fields.values(), task_id))
        updated = await execute_one(db, "SELECT * FROM work_job_tasks WHERE id = ?", (task_id,))
        updated["params"] = from_json(updated["params"]) or {}
        updated["tools_used"] = from_json(updated["tools_used"]) or []
        updated["measured_values"] = from_json(updated["measured_values"]) or {}
        updated["chart_data"] = from_json(updated["chart_data"]) or []
        return updated


@app.delete("/api/work-jobs/{job_id}/tasks/{task_id}")
async def delete_task(job_id: int, task_id: int, admin: bool = False):
    """Delete a task record (admin only)"""
    if not admin:
        raise HTTPException(403, "Only admin can delete task records")
    async with get_db() as db:
        rows = await execute_update(db,
            "DELETE FROM work_job_tasks WHERE id = ? AND work_job_id = ?", (task_id, job_id))
        if rows == 0:
            raise HTTPException(404, "Task not found")
        return {"status": "ok"}


# -- Sessions (legacy, read-only — sourced from work_jobs) --

@app.get("/api/sessions")
async def get_sessions():
    async with get_db() as db:
        jobs = await execute_all(db, "SELECT * FROM work_jobs ORDER BY started_at DESC LIMIT 20")
        return [{"id": j["id"], "station_id": j["station_id"],
                 "recipe_name": j["recipe_name"], "start_time": j["started_at"],
                 "end_time": j["completed_at"], "status": j["status"],
                 "battery_serial": j["battery_serial"]} for j in jobs]


@app.get("/api/sessions/")
async def get_sessions_slash():
    return await get_sessions()


# -- Reports --

@app.get("/api/reports/{job_id}")
async def get_report(job_id: int):
    """Get assembled report data for a work job"""
    async with get_db() as db:
        j = await execute_one(db, "SELECT * FROM work_jobs WHERE id = ?", (job_id,))
        if not j:
            raise HTTPException(404, "Work job not found")
        tasks = await execute_all(db,
            "SELECT * FROM work_job_tasks WHERE work_job_id = ? ORDER BY task_number", (job_id,))
        tools_map = {}
        for t in tasks:
            t["params"] = from_json(t["params"]) or {}
            t["tools_used"] = from_json(t["tools_used"]) or []
            t["measured_values"] = from_json(t["measured_values"]) or {}
            t["chart_data"] = from_json(t["chart_data"]) or []
            for tool in t["tools_used"]:
                tid = tool.get("tool_id")
                if tid and tid not in tools_map:
                    tools_map[tid] = tool
        j["tasks"] = tasks
        return {
            "job": j,
            "tools_used_summary": list(tools_map.values()),
            "task_count": len(tasks),
            "generated_at": datetime.now().isoformat(),
        }


@app.post("/api/reports/{job_id}/generate")
async def generate_report(job_id: int):
    return {"status": "ok", "message": f"Report generated for job {job_id}"}


# -- Admin --

@app.get("/api/admin/system/info")
async def system_info():
    return {
        "version": "1.4.1-mock",
        "mode": "UI/UX Testing (Mock Backend)",
        "stations": 12,
        "uptime_s": 3600,
        "platform": "Windows 11",
        "python": "3.11",
        "hardware_connected": False,
        "i2c_bus": "MOCK",
        "psu_count": 0,
        "load_count": 0,
    }


@app.get("/api/admin/system/health")
async def system_health():
    return {
        "status": "healthy",
        "mode": "mock",
        "database": "ok",
        "influxdb": "mock",
        "i2c": "mock",
        "psu_connections": 0,
        "load_connections": 0,
        "websocket_clients": len(_ws_clients),
    }


# =============================================================================
# Serve Frontend Build (production)
# =============================================================================

from pathlib import Path as _Path

_frontend_build = _Path(__file__).parent.parent / "frontend" / "build"
if _frontend_build.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_build), html=True), name="static")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    _host_ip = "0.0.0.0"
    _port = 8000
    _has_frontend = _frontend_build.exists()
    print("\n  Battery Test Bench - Mock Server (UI/UX Testing)")
    print("  ================================================")
    print(f"  Backend:   http://localhost:{_port}")
    if _has_frontend:
        print(f"  Frontend:  http://localhost:{_port}  (served from build/)")
    else:
        print("  Frontend:  http://localhost:3001 (run 'npm run dev' in frontend/)")
    print("  Database:  SQLite (backend/data/battery_bench.db)")
    print("  Seed data: 12 stations, 5 customers, 5 work orders, 7 profiles, 3 tech pubs, 8 recipes, 6 tools")
    print(f"  WebSocket: ws://localhost:{_port}/api/ws/live")
    print()

    uvicorn.run(app, host=_host_ip, port=_port, log_level="info")
