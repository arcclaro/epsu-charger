"""
Battery Test Bench - Tech Pubs (CMM) API
Version: 1.0.0

Changelog:
v1.0.0 (2026-02-22): Full CRUD + applicability bulk replace
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db, execute_one, execute_all

router = APIRouter(prefix="/tech-pubs", tags=["tech-pubs"])


# -- Pydantic Models --

class TechPubCreate(BaseModel):
    cmm_number: str
    title: str
    revision: Optional[str] = None
    revision_date: Optional[str] = None
    ata_chapter: Optional[str] = None
    manufacturer: Optional[str] = None
    issued_by: Optional[str] = None
    notes: Optional[str] = None


class TechPubUpdate(BaseModel):
    cmm_number: Optional[str] = None
    title: Optional[str] = None
    revision: Optional[str] = None
    revision_date: Optional[str] = None
    ata_chapter: Optional[str] = None
    manufacturer: Optional[str] = None
    issued_by: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ApplicabilityEntry(BaseModel):
    part_number: str
    service_type: str = "inspection_test"


# -- Helpers --

async def _enrich_tech_pub(db, row: dict) -> dict:
    """Add applicability and manufacturer fallback to a tech pub row."""
    tp = dict(row)
    tp["manufacturer"] = tp.get("manufacturer") or tp.get("issued_by")
    apps = await execute_all(
        db,
        "SELECT part_number, service_type FROM tech_pub_applicability WHERE tech_pub_id = ?",
        (tp["id"],)
    )
    tp["applicability"] = apps
    return tp


# -- Endpoints --

@router.get("/")
async def list_tech_pubs():
    """List all tech pubs with applicability rows."""
    async with get_db() as db:
        rows = await execute_all(
            db, "SELECT * FROM tech_pubs WHERE is_active = 1 ORDER BY cmm_number"
        )
        return [await _enrich_tech_pub(db, row) for row in rows]


@router.get("/match/{part_number}")
async def match_tech_pub(part_number: str):
    """Find tech pub matching a part number via applicability table."""
    async with get_db() as db:
        row = await execute_one(db, """
            SELECT tp.* FROM tech_pubs tp
            JOIN tech_pub_applicability tpa ON tpa.tech_pub_id = tp.id
            WHERE tpa.part_number = ? AND tp.is_active = 1
            LIMIT 1
        """, (part_number,))
        if not row:
            raise HTTPException(status_code=404, detail="No tech pub found for part number")
        return await _enrich_tech_pub(db, row)


@router.get("/{tp_id}")
async def get_tech_pub(tp_id: int):
    """Get single tech pub with applicability."""
    async with get_db() as db:
        row = await execute_one(db, "SELECT * FROM tech_pubs WHERE id = ?", (tp_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Tech pub not found")
        return await _enrich_tech_pub(db, row)


@router.post("/")
async def create_tech_pub(data: TechPubCreate):
    """Create a new tech pub."""
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO tech_pubs (cmm_number, title, revision, revision_date,
                                   ata_chapter, manufacturer, issued_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.cmm_number, data.title, data.revision, data.revision_date,
            data.ata_chapter, data.manufacturer or data.issued_by,
            data.issued_by or data.manufacturer, data.notes
        ))
        await db.commit()
        tp_id = cursor.lastrowid
        row = await execute_one(db, "SELECT * FROM tech_pubs WHERE id = ?", (tp_id,))
        return await _enrich_tech_pub(db, row)


@router.put("/{tp_id}")
async def update_tech_pub(tp_id: int, data: TechPubUpdate):
    """Update an existing tech pub."""
    async with get_db() as db:
        existing = await execute_one(db, "SELECT * FROM tech_pubs WHERE id = ?", (tp_id,))
        if not existing:
            raise HTTPException(status_code=404, detail="Tech pub not found")

        updates = []
        params = []
        for field_name, value in data.model_dump(exclude_none=True).items():
            updates.append(f"{field_name} = ?")
            params.append(value)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(tp_id)

        await db.execute(
            f"UPDATE tech_pubs SET {', '.join(updates)} WHERE id = ?", params
        )
        await db.commit()

        row = await execute_one(db, "SELECT * FROM tech_pubs WHERE id = ?", (tp_id,))
        return await _enrich_tech_pub(db, row)


@router.delete("/{tp_id}")
async def delete_tech_pub(tp_id: int):
    """Delete a tech pub and cascade applicability."""
    async with get_db() as db:
        existing = await execute_one(db, "SELECT id FROM tech_pubs WHERE id = ?", (tp_id,))
        if not existing:
            raise HTTPException(status_code=404, detail="Tech pub not found")

        await db.execute("DELETE FROM tech_pub_applicability WHERE tech_pub_id = ?", (tp_id,))
        await db.execute("DELETE FROM tech_pubs WHERE id = ?", (tp_id,))
        await db.commit()
        return {"status": "ok"}


@router.put("/{tp_id}/applicability")
async def bulk_replace_applicability(tp_id: int, entries: List[ApplicabilityEntry]):
    """Bulk replace applicability rows for a tech pub."""
    async with get_db() as db:
        existing = await execute_one(db, "SELECT id FROM tech_pubs WHERE id = ?", (tp_id,))
        if not existing:
            raise HTTPException(status_code=404, detail="Tech pub not found")

        await db.execute("DELETE FROM tech_pub_applicability WHERE tech_pub_id = ?", (tp_id,))
        for entry in entries:
            await db.execute("""
                INSERT INTO tech_pub_applicability (tech_pub_id, part_number, service_type)
                VALUES (?, ?, ?)
            """, (tp_id, entry.part_number, entry.service_type))
        await db.commit()
        return {"status": "ok", "count": len(entries)}
