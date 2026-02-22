"""
Battery Test Bench - Battery Profile API Endpoints
Version: 1.2.1

Changelog:
v1.2.1 (2026-02-16): Initial battery profile CRUD for service shop model
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import aiosqlite
import logging

from config import settings

router = APIRouter(prefix="/battery-profiles", tags=["battery-profiles"])
logger = logging.getLogger(__name__)


class BatteryProfileCreate(BaseModel):
    part_number: str
    amendment: Optional[str] = None
    description: Optional[str] = None
    manufacturer: str = "DIEHL Aerospace GmbH"

    nominal_voltage_v: float
    capacity_ah: float
    num_cells: int
    chemistry: str = "NiCd"

    std_charge_current_ma: int
    std_charge_duration_h: float
    std_charge_voltage_limit_mv: int
    std_charge_temp_max_c: float = 45.0

    cap_test_current_a: float
    cap_test_voltage_min_mv: int
    cap_test_duration_min: int
    cap_test_temp_max_c: float = 45.0

    fast_charge_enabled: bool = False
    fast_charge_current_a: Optional[float] = None
    fast_charge_max_duration_min: Optional[int] = None
    fast_charge_delta_v_mv: Optional[int] = None

    trickle_charge_current_ma: Optional[int] = None
    trickle_charge_voltage_max_mv: Optional[int] = None

    partial_charge_duration_h: Optional[float] = None

    rest_period_age_threshold_months: int = 24
    rest_period_duration_h: int = 24

    emergency_temp_max_c: float = 60.0
    emergency_temp_min_c: float = -20.0

    notes: Optional[str] = None


@router.get("/")
async def list_profiles(active_only: bool = True):
    """List all battery profiles"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM battery_profiles"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY part_number, amendment"
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/{profile_id}")
async def get_profile(profile_id: int):
    """Get a specific battery profile"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM battery_profiles WHERE id = ?",
            (profile_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")
        return dict(row)


@router.get("/by-part/{part_number}")
async def get_profile_by_part(part_number: str,
                               amendment: Optional[str] = None):
    """Look up battery profile by part number and amendment"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if amendment:
            cursor = await db.execute("""
                SELECT * FROM battery_profiles
                WHERE part_number = ? AND amendment = ? AND is_active = 1
            """, (part_number, amendment))
        else:
            cursor = await db.execute("""
                SELECT * FROM battery_profiles
                WHERE part_number = ? AND is_active = 1
                ORDER BY amendment DESC LIMIT 1
            """, (part_number,))

        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404,
                              detail=f"No profile for {part_number}")
        return dict(row)


@router.post("/")
async def create_profile(data: BatteryProfileCreate):
    """Create a new battery profile"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        try:
            cursor = await db.execute("""
                INSERT INTO battery_profiles (
                    part_number, amendment, description, manufacturer,
                    nominal_voltage_v, capacity_ah, num_cells, chemistry,
                    std_charge_current_ma, std_charge_duration_h,
                    std_charge_voltage_limit_mv, std_charge_temp_max_c,
                    cap_test_current_a, cap_test_voltage_min_mv,
                    cap_test_duration_min, cap_test_temp_max_c,
                    fast_charge_enabled, fast_charge_current_a,
                    fast_charge_max_duration_min, fast_charge_delta_v_mv,
                    trickle_charge_current_ma, trickle_charge_voltage_max_mv,
                    partial_charge_duration_h,
                    rest_period_age_threshold_months, rest_period_duration_h,
                    emergency_temp_max_c, emergency_temp_min_c,
                    notes
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?,
                    ?, ?,
                    ?, ?,
                    ?
                )
            """, (
                data.part_number, data.amendment, data.description,
                data.manufacturer,
                data.nominal_voltage_v, data.capacity_ah, data.num_cells,
                data.chemistry,
                data.std_charge_current_ma, data.std_charge_duration_h,
                data.std_charge_voltage_limit_mv, data.std_charge_temp_max_c,
                data.cap_test_current_a, data.cap_test_voltage_min_mv,
                data.cap_test_duration_min, data.cap_test_temp_max_c,
                data.fast_charge_enabled, data.fast_charge_current_a,
                data.fast_charge_max_duration_min, data.fast_charge_delta_v_mv,
                data.trickle_charge_current_ma,
                data.trickle_charge_voltage_max_mv,
                data.partial_charge_duration_h,
                data.rest_period_age_threshold_months,
                data.rest_period_duration_h,
                data.emergency_temp_max_c, data.emergency_temp_min_c,
                data.notes
            ))
            await db.commit()

            return {
                "id": cursor.lastrowid,
                "message": f"Profile for {data.part_number} created"
            }
        except aiosqlite.IntegrityError:
            raise HTTPException(
                status_code=400,
                detail=f"Profile for {data.part_number} / {data.amendment} already exists"
            )


@router.delete("/{profile_id}")
async def delete_profile(profile_id: int):
    """Soft-delete a battery profile"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        await db.execute(
            "UPDATE battery_profiles SET is_active = 0 WHERE id = ?",
            (profile_id,)
        )
        await db.commit()
        return {"success": True, "message": f"Profile {profile_id} deactivated"}
