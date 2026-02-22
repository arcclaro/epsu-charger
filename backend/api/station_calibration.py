"""
Battery Test Bench - Station Calibration / Verification API
Version: 1.0.0

Changelog:
v1.0.0 (2026-02-22): Station equipment verification data
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import date, datetime

from database import get_db, execute_one, execute_all

router = APIRouter(prefix="/station-calibration", tags=["station-calibration"])


async def _build_station_verification(db, station_id: int) -> dict:
    """Build a StationVerification-shaped object for one station."""
    result = {
        "station_id": station_id,
        "psu_last_cal": None,
        "psu_next_cal": None,
        "psu_cal_status": None,
        "psu_model": None,
        "psu_serial": None,
        "dc_load_last_cal": None,
        "dc_load_next_cal": None,
        "dc_load_cal_status": None,
        "dc_load_model": None,
        "dc_load_serial": None,
    }

    # Get calibration data for PSU and DC Load
    cals = await execute_all(
        db,
        "SELECT * FROM station_calibrations WHERE station_id = ?",
        (station_id,)
    )
    for cal in cals:
        unit = cal["unit"]
        prefix = "psu" if unit == "psu" else "dc_load"
        result[f"{prefix}_last_cal"] = cal.get("last_calibration_date")
        result[f"{prefix}_next_cal"] = cal.get("next_due_date")
        result[f"{prefix}_model"] = cal.get("model")
        result[f"{prefix}_serial"] = cal.get("serial_number")
        # Compute status
        next_due = cal.get("next_due_date")
        if next_due:
            try:
                due_date = date.fromisoformat(next_due)
                if due_date < date.today():
                    result[f"{prefix}_cal_status"] = "expired"
                else:
                    result[f"{prefix}_cal_status"] = "valid"
            except (ValueError, TypeError):
                result[f"{prefix}_cal_status"] = "unknown"
        else:
            result[f"{prefix}_cal_status"] = "unknown"

    # Supplement with station_equipment if calibration records lack model/serial
    equip_rows = await execute_all(
        db,
        "SELECT * FROM station_equipment WHERE station_id = ? AND is_active = 1",
        (station_id,)
    )
    for eq in equip_rows:
        role = eq["equipment_role"]
        if role == "psu":
            if not result["psu_model"] and eq.get("model"):
                result["psu_model"] = eq["model"]
            if not result["psu_serial"] and eq.get("serial_number"):
                result["psu_serial"] = eq["serial_number"]
        elif role == "dc_load":
            if not result["dc_load_model"] and eq.get("model"):
                result["dc_load_model"] = eq["model"]
            if not result["dc_load_serial"] and eq.get("serial_number"):
                result["dc_load_serial"] = eq["serial_number"]

    return result


@router.get("/procedures/psu")
async def psu_cal_procedure():
    """PSU calibration procedure (placeholder)."""
    return []


@router.get("/procedures/dc-load")
async def dc_load_cal_procedure():
    """DC Load calibration procedure (placeholder)."""
    return []


@router.get("/")
async def list_station_calibrations():
    """List verification data for all 12 stations."""
    async with get_db() as db:
        return [await _build_station_verification(db, sid) for sid in range(1, 13)]


@router.get("/{station_id}")
async def get_station_calibration(station_id: int):
    """Get verification data for a single station."""
    if not 1 <= station_id <= 12:
        raise HTTPException(status_code=400, detail="Station ID must be 1-12")
    async with get_db() as db:
        return await _build_station_verification(db, station_id)


@router.put("/{station_id}/{unit}")
async def update_station_calibration(station_id: int, unit: str, data: dict):
    """Upsert calibration record for a station unit (psu or dc_load)."""
    if not 1 <= station_id <= 12:
        raise HTTPException(status_code=400, detail="Station ID must be 1-12")
    if unit not in ("psu", "dc_load"):
        raise HTTPException(status_code=400, detail="Unit must be 'psu' or 'dc_load'")

    async with get_db() as db:
        now = datetime.now().isoformat()
        await db.execute("""
            INSERT INTO station_calibrations
                (station_id, unit, model, serial_number,
                 last_calibration_date, next_due_date,
                 calibrated_by, calibration_certificate, result, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(station_id, unit) DO UPDATE SET
                model = COALESCE(excluded.model, model),
                serial_number = COALESCE(excluded.serial_number, serial_number),
                last_calibration_date = COALESCE(excluded.last_calibration_date, last_calibration_date),
                next_due_date = COALESCE(excluded.next_due_date, next_due_date),
                calibrated_by = COALESCE(excluded.calibrated_by, calibrated_by),
                calibration_certificate = COALESCE(excluded.calibration_certificate, calibration_certificate),
                result = COALESCE(excluded.result, result),
                updated_at = excluded.updated_at
        """, (
            station_id, unit,
            data.get("model"), data.get("serial_number"),
            data.get("last_calibration_date"), data.get("next_due_date"),
            data.get("calibrated_by"), data.get("calibration_certificate"),
            data.get("result"), now
        ))
        await db.commit()
        return await _build_station_verification(db, station_id)
