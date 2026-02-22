"""
Battery Test Bench - Tools API
Version: 1.0.0

Changelog:
v1.0.0 (2026-02-22): Full CRUD with verification enrichment
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date, timedelta

from database import get_db, execute_one, execute_all

router = APIRouter(prefix="/tools", tags=["tools"])


# -- Pydantic Models --

class ToolCreate(BaseModel):
    part_number: str
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: str
    calibration_date: Optional[str] = None
    verification_date: Optional[str] = None
    verification_cycle_days: Optional[int] = 180
    internal_reference: Optional[str] = None
    tool_id_display: Optional[str] = None
    tcp_ip_address: Optional[str] = None
    designated_station: Optional[int] = None
    category: Optional[str] = None
    calibration_certificate: Optional[str] = None
    calibrated_by: Optional[str] = None


class ToolUpdate(BaseModel):
    part_number: Optional[str] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    calibration_date: Optional[str] = None
    verification_date: Optional[str] = None
    verification_cycle_days: Optional[int] = None
    valid_until: Optional[str] = None
    internal_reference: Optional[str] = None
    tool_id_display: Optional[str] = None
    tcp_ip_address: Optional[str] = None
    designated_station: Optional[int] = None
    category: Optional[str] = None
    calibration_certificate: Optional[str] = None
    calibrated_by: Optional[str] = None
    is_active: Optional[bool] = None


# -- Helpers --

def _enrich_tool(row: dict) -> dict:
    """Add computed fields: verification_date alias, tool_id_display, valid_until."""
    t = dict(row)
    # verification_date is an alias for calibration_date
    if not t.get("verification_date") and t.get("calibration_date"):
        t["verification_date"] = t["calibration_date"]
    # tool_id_display default
    if not t.get("tool_id_display"):
        t["tool_id_display"] = f"TID{t['id']:03d}"
    # Compute valid_until from verification_date + cycle days
    vd = t.get("verification_date") or t.get("calibration_date")
    cycle = t.get("verification_cycle_days") or 180
    if vd and not t.get("valid_until"):
        try:
            vd_date = date.fromisoformat(vd[:10])
            t["valid_until"] = (vd_date + timedelta(days=cycle)).isoformat()
        except (ValueError, TypeError):
            pass
    return t


# -- Endpoints --

@router.get("/")
async def list_tools(category: Optional[str] = None):
    """List tools, optionally filter by category."""
    async with get_db() as db:
        if category:
            rows = await execute_all(
                db,
                "SELECT * FROM tools WHERE is_active = 1 AND category = ? ORDER BY id",
                (category,)
            )
        else:
            rows = await execute_all(
                db, "SELECT * FROM tools WHERE is_active = 1 ORDER BY id"
            )
        return [_enrich_tool(row) for row in rows]


@router.get("/valid")
async def list_valid_tools(category: Optional[str] = None):
    """List tools where valid_until >= today."""
    today = date.today().isoformat()
    async with get_db() as db:
        base_sql = """
            SELECT * FROM tools WHERE is_active = 1
            AND (valid_until >= ? OR valid_until IS NULL)
        """
        params: list = [today]
        if category:
            base_sql += " AND category = ?"
            params.append(category)
        base_sql += " ORDER BY id"
        rows = await execute_all(db, base_sql, params)
        return [_enrich_tool(row) for row in rows]


@router.get("/{tool_id}")
async def get_tool(tool_id: int):
    """Get single tool."""
    async with get_db() as db:
        row = await execute_one(db, "SELECT * FROM tools WHERE id = ?", (tool_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Tool not found")
        return _enrich_tool(row)


@router.post("/")
async def create_tool(data: ToolCreate):
    """Create a new tool."""
    async with get_db() as db:
        # Compute valid_until
        vd = data.verification_date or data.calibration_date
        cycle = data.verification_cycle_days or 180
        valid_until = None
        if vd:
            try:
                valid_until = (date.fromisoformat(vd[:10]) + timedelta(days=cycle)).isoformat()
            except (ValueError, TypeError):
                pass

        cursor = await db.execute("""
            INSERT INTO tools (part_number, description, manufacturer, serial_number,
                               calibration_date, verification_date, verification_cycle_days,
                               valid_until, internal_reference, tool_id_display,
                               tcp_ip_address, designated_station, category,
                               calibration_certificate, calibrated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.part_number, data.description, data.manufacturer, data.serial_number,
            data.calibration_date, vd, cycle,
            valid_until, data.internal_reference, data.tool_id_display,
            data.tcp_ip_address, data.designated_station, data.category,
            data.calibration_certificate, data.calibrated_by
        ))
        await db.commit()
        row = await execute_one(db, "SELECT * FROM tools WHERE id = ?", (cursor.lastrowid,))
        return _enrich_tool(row)


@router.put("/{tool_id}")
async def update_tool(tool_id: int, data: ToolUpdate):
    """Update an existing tool."""
    async with get_db() as db:
        existing = await execute_one(db, "SELECT * FROM tools WHERE id = ?", (tool_id,))
        if not existing:
            raise HTTPException(status_code=404, detail="Tool not found")

        updates = []
        params = []
        for field_name, value in data.model_dump(exclude_none=True).items():
            updates.append(f"{field_name} = ?")
            params.append(value)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(tool_id)

        await db.execute(
            f"UPDATE tools SET {', '.join(updates)} WHERE id = ?", params
        )
        await db.commit()
        row = await execute_one(db, "SELECT * FROM tools WHERE id = ?", (tool_id,))
        return _enrich_tool(row)


@router.delete("/{tool_id}")
async def delete_tool(tool_id: int):
    """Soft-delete a tool (is_active = 0)."""
    async with get_db() as db:
        existing = await execute_one(db, "SELECT id FROM tools WHERE id = ?", (tool_id,))
        if not existing:
            raise HTTPException(status_code=404, detail="Tool not found")

        await db.execute(
            "UPDATE tools SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), tool_id)
        )
        await db.commit()
        return {"status": "ok"}
